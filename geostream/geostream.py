import typing as typ
import io
import struct
import gzip
import json
import geojson


GEOJSON_EPSG_SRID: int = 4326  # per IETF RFC 7946 August 2016, geojson nominal coordinate reference is WGS-84
GEOSTREAM_SCHEMA_VERSIONS: typ.Sequence[int] = (3,)


class GeoStreamReader(typ.Iterator[geojson.Feature]):
    """ Stream header accessors and iterator over a readable binary stream of compressed GeoJSON Features """

    def __init__(self, stream: typ.BinaryIO) -> None:
        self.stream: typ.BinaryIO = stream
        self._schema_version, self._srid, self._props = self._read_stream_header()

    def __iter__(self) -> "GeoStreamReader":
        return self

    def __next__(self) -> geojson.Feature:
        get_next = self._reader()
        if get_next is None:
            raise StopIteration()
        else:
            return get_next

    def _read_stream_header(
        self
    ) -> typ.Tuple[int, int, typ.Optional[typ.Mapping[str, typ.Any]]]:
        self.stream.seek(0, io.SEEK_SET)  # header is located at the start of the stream
        version, srid, props_len = struct.unpack(
            "Bii", self.stream.read(struct.calcsize("Bii"))
        )

        if version not in GEOSTREAM_SCHEMA_VERSIONS:
            raise ValueError(
                f"GeoStream schema version: {version} not supported, expected one of: {GEOSTREAM_SCHEMA_VERSIONS}"
            )

        props: typ.Optional[typ.Mapping[str, typ.Any]] = None
        if props_len > 0:
            buffer: bytes = self.stream.read(props_len)
            props = json.loads(buffer)

        return version, srid, props

    def _read_length(self) -> typ.Optional[int]:
        fmt = "i"
        read_len = struct.calcsize(fmt)
        buffer: bytes = self.stream.read(read_len)
        return struct.unpack(fmt, buffer)[0] if len(buffer) == read_len else None

    def _reader(self) -> typ.Optional[geojson.Feature]:
        zip_len = self._read_length()
        if zip_len is not None:
            zip_data: bytes = self.stream.read(zip_len)
            if self._schema_version > 2:
                _ = self._read_length()
            if zip_data and len(zip_data) == zip_len:
                unzipped: bytes = gzip.decompress(zip_data)
                return geojson.loads(unzipped)
            else:
                return None  # unexpected eof after length
        else:
            return None  # normal eof

    @property
    def schema_version(self) -> int:
        return self._schema_version

    @property
    def srid(self) -> int:
        return self._srid

    @property
    def properties(self) -> typ.Optional[typ.Mapping[str, typ.Any]]:
        return self._props


class GeoStreamReverseReader(GeoStreamReader):
    """ Stream header accessors and backwards iterator over a readable binary stream of compressed GeoJSON Features """

    LENGTH_SIZE: int = struct.calcsize("i")

    def __init__(
        self, stream: typ.BinaryIO, buf_size: int = io.DEFAULT_BUFFER_SIZE
    ) -> None:
        super().__init__(stream)
        self.buf_size = buf_size
        self.end_of_header_offset = stream.tell()
        self.end_of_stream_offset = self.stream.seek(0, io.SEEK_END)
        self.data_size = self.end_of_stream_offset - self.end_of_header_offset
        self.remaining_size = self.data_size
        self.offset_from_stream_end = 0
        self.buffer = io.BytesIO()

    def _grow_buffer(self):
        if self.remaining_size > 0:
            cur_buffer_offset = self.buffer.tell()
            self.buffer.seek(0, io.SEEK_SET)
            leftover: bytes = self.buffer.read(cur_buffer_offset)
            self.offset_from_stream_end = min(
                self.data_size, (self.offset_from_stream_end + self.buf_size)
            )
            self.stream.seek(-self.offset_from_stream_end, io.SEEK_END)
            self.buffer = io.BytesIO(
                self.stream.read(min(self.remaining_size, self.buf_size))
            )
            self.remaining_size -= self.buf_size
            self.buffer.seek(0, io.SEEK_END)
            self.buffer.write(leftover)

    def _read_length(self) -> typ.Optional[int]:
        len_buffer: bytes = self.buffer.read(GeoStreamReverseReader.LENGTH_SIZE)
        return (
            struct.unpack("i", len_buffer)[0]
            if len(len_buffer) == GeoStreamReverseReader.LENGTH_SIZE
            else None
        )

    def _reader(self) -> typ.Optional[geojson.Feature]:
        if self.buffer.tell() < GeoStreamReverseReader.LENGTH_SIZE:
            self._grow_buffer()
            if self.buffer.tell() < GeoStreamReverseReader.LENGTH_SIZE:
                return (
                    None
                )  # malformed stream - couldn't get enough bytes to read the next feature length

        self.buffer.seek(-GeoStreamReverseReader.LENGTH_SIZE, io.SEEK_CUR)
        zip_len = self._read_length()
        if zip_len is None:
            return None  # should never get here

        next_feature: typ.Optional[geojson.Feature] = None
        envelope_size: int = zip_len + (GeoStreamReverseReader.LENGTH_SIZE * 2)

        while envelope_size > self.buffer.tell():
            self._grow_buffer()
            if self.remaining_size <= 0 and envelope_size > self.buffer.tell():
                return (
                    None
                )  # malformed stream - missing feature data or corrupted length

        next_relative_offset: int = GeoStreamReverseReader.LENGTH_SIZE + zip_len
        self.buffer.seek(-next_relative_offset, io.SEEK_CUR)
        zip_data: bytes = self.buffer.read(zip_len)
        if zip_data and len(zip_data) == zip_len:
            unzipped: bytes = gzip.decompress(zip_data)
            next_feature = geojson.loads(unzipped)

        self.buffer.seek(-next_relative_offset, io.SEEK_CUR)
        return next_feature


class GeoStreamWriter:
    """ Binary stream writer provides methods to write a header followed by compressed GeoJSON Features  """

    GEOSTREAM_SCHEMA_VERSION: int = 3

    def __init__(
        self,
        stream: typ.BinaryIO,
        props: typ.Optional[typ.Mapping[str, typ.Any]] = None,
        srid: int = GEOJSON_EPSG_SRID,
    ) -> None:
        self.stream: typ.BinaryIO = stream
        self._write_header(srid, props)

    def _write_header(
        self, srid: int, props: typ.Optional[typ.Mapping[str, typ.Any]] = None
    ) -> None:
        """ Only write the header if at the start of the stream - allowing appending to a stream in progress """
        if self.stream.tell() == 0:
            properties: typ.Optional[bytes] = json.dumps(
                props
            ).encode() if props else None
            props_len = len(properties) if properties else 0
            self.stream.write(
                struct.pack(
                    "Bii", GeoStreamWriter.GEOSTREAM_SCHEMA_VERSION, srid, props_len
                )
            )
            if properties is not None:
                self.stream.write(properties)

    def write_feature(self, feature: geojson.Feature) -> None:
        """ Write a geojson feature as a compressed GeoJSON feature """
        gjson: geojson.Feature = feature
        unzipped: str = geojson.dumps(gjson)
        zipped_data: bytes = gzip.compress(unzipped.encode())
        zip_len: int = len(zipped_data)
        self.stream.write(struct.pack("i", zip_len))
        self.stream.write(zipped_data)
        self.stream.write(struct.pack("i", zip_len))

    def write_feature_collection(self, collection: geojson.FeatureCollection) -> None:
        """ Write all features from a geojson feature collection as compressed GeoJSON features """
        for feature in collection.features:
            self.write_feature(feature)


def reader(
    stream: typ.BinaryIO,
    reverse: bool = False,
    rev_buf_size: int = io.DEFAULT_BUFFER_SIZE,
) -> GeoStreamReader:
    """
    Return a geojson Feature iterator that reads and unpacks compressed GeoJSON features from the stream
    until the features are exhausted, and provides properties to access the unpacked header data
    :param stream: Readable Binary IO object
    :param reverse: Flag to reverse the order of iteration from the end of the stream. Default: False
    :param rev_buf_size: Buffer length for reverse iterator
    :return: GeoStreamReader object
    """
    if reverse is False:
        return GeoStreamReader(stream)
    else:
        return GeoStreamReverseReader(stream, buf_size=rev_buf_size)


def writer(
    stream: typ.BinaryIO,
    props: typ.Optional[typ.Mapping[str, typ.Any]] = None,
    srid: int = GEOJSON_EPSG_SRID,
) -> GeoStreamWriter:
    """
    Return a writer that translates a feature/feature collection into compressed GeoJSON Feature(s) that
    are written to the binary stream
    :param stream: Random writable Binary IO object
    :param props: (Optional) Dictionary of properties to add to the header. Default: None
    :param srid: (Optional) EPSG SRID integer for the GeoJSON x, y coordinates geographic reference.
    Default: Defined in the constant: GEOJSON_EPSG_SRID
    :return: GeoStreamWriter object
    """
    return GeoStreamWriter(stream, props, srid=srid)
