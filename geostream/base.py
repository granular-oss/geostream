import abc
import io
import struct
import typing as typ
from functools import partial

from geostream.constants import GEOJSON_EPSG_SRID, GEOSTREAM_SCHEMA_VERSIONS
from geostream.feature import Feature, FeatureCollection, Properties


class Header(typ.NamedTuple):
    version: int
    srid: int
    props_len: int


def read_header(stream: typ.BinaryIO) -> Header:
    stream.seek(0, io.SEEK_SET)  # header is located at the start of the stream
    header = Header(*struct.unpack("Bii", stream.read(struct.calcsize("Bii"))))
    version = header.version
    if version not in GEOSTREAM_SCHEMA_VERSIONS:
        raise ValueError(
            f"GeoStream schema version: {version} not supported, expected one of: {GEOSTREAM_SCHEMA_VERSIONS}"
        )

    return header


class GeoStreamReader(typ.Iterator[Feature]):
    """ Stream header accessors and iterator over a readable binary stream of compressed GeoJSON Features """

    __slots__ = ("stream", "_schema_version", "_srid", "_props", "_construct_feature")
    GEOSTREAM_SCHEMA_VERSION: int

    def __init__(self, stream: typ.BinaryIO) -> None:
        self.stream: typ.BinaryIO = stream
        self._schema_version, self._srid, self._props = self._read_stream_header()
        self._construct_feature = partial(Feature.from_dict, srid=self._srid)

    def __iter__(self) -> "GeoStreamReader":
        return self

    def __next__(self) -> Feature:
        get_next = self._reader()
        if get_next is None:
            raise StopIteration()
        else:
            return get_next

    @abc.abstractmethod
    def _load_properties(self, buffer: bytes) -> Properties:
        ...

    @abc.abstractmethod
    def _load_feature(self, data: bytes) -> Feature:
        ...

    def _read_stream_header(self) -> typ.Tuple[int, int, typ.Optional[Properties]]:
        version, srid, props_len = read_header(self.stream)
        if version != self.GEOSTREAM_SCHEMA_VERSION:
            raise ValueError(
                f"GeoStream schema version: {version} not supported, expected: {self.GEOSTREAM_SCHEMA_VERSION}"
            )
        props: typ.Optional[typ.Mapping[str, typ.Any]] = None
        if props_len > 0:
            buffer: bytes = self.stream.read(props_len)
            props = self._load_properties(buffer)

        return version, srid, props

    def _read_length(self) -> typ.Optional[int]:
        fmt = "i"
        read_len = struct.calcsize(fmt)
        buffer: bytes = self.stream.read(read_len)
        return struct.unpack(fmt, buffer)[0] if len(buffer) == read_len else None

    def _reader(self) -> typ.Optional[Feature]:
        zip_len = self._read_length()
        if zip_len is not None:
            zip_data: bytes = self.stream.read(zip_len)
            _ = self._read_length()
            if zip_data and len(zip_data) == zip_len:
                return self._load_feature(zip_data)
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

    __slots__ = (
        "buf_size",
        "end_of_header_offset",
        "end_of_stream_offset",
        "data_size",
        "remaining_size",
        "offset_from_stream_end",
        "buffer",
    )
    LENGTH_SIZE: int = struct.calcsize("i")

    def __init__(self, stream: typ.BinaryIO, buf_size: int = io.DEFAULT_BUFFER_SIZE) -> None:
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
            self.offset_from_stream_end = min(self.data_size, (self.offset_from_stream_end + self.buf_size))
            self.stream.seek(-self.offset_from_stream_end, io.SEEK_END)
            self.buffer = io.BytesIO(self.stream.read(min(self.remaining_size, self.buf_size)))
            self.remaining_size -= self.buf_size
            self.buffer.seek(0, io.SEEK_END)
            self.buffer.write(leftover)

    def _read_length(self) -> typ.Optional[int]:
        len_buffer: bytes = self.buffer.read(GeoStreamReverseReader.LENGTH_SIZE)
        return struct.unpack("i", len_buffer)[0] if len(len_buffer) == GeoStreamReverseReader.LENGTH_SIZE else None

    def _reader(self) -> typ.Optional[Feature]:
        if self.buffer.tell() < GeoStreamReverseReader.LENGTH_SIZE:
            self._grow_buffer()
            if self.buffer.tell() < GeoStreamReverseReader.LENGTH_SIZE:
                return None  # malformed stream - couldn't get enough bytes to read the next feature length

        self.buffer.seek(-GeoStreamReverseReader.LENGTH_SIZE, io.SEEK_CUR)
        zip_len = self._read_length()
        if zip_len is None:
            return None  # should never get here

        next_feature: typ.Optional[Feature] = None
        envelope_size: int = zip_len + (GeoStreamReverseReader.LENGTH_SIZE * 2)

        while envelope_size > self.buffer.tell():
            self._grow_buffer()
            if self.remaining_size <= 0 and envelope_size > self.buffer.tell():
                return None  # malformed stream - missing feature data or corrupted length

        next_relative_offset: int = GeoStreamReverseReader.LENGTH_SIZE + zip_len
        self.buffer.seek(-next_relative_offset, io.SEEK_CUR)
        zip_data: bytes = self.buffer.read(zip_len)
        if zip_data and len(zip_data) == zip_len:
            next_feature = self._load_feature(zip_data)

        self.buffer.seek(-next_relative_offset, io.SEEK_CUR)
        return next_feature


class GeoStreamWriter:
    """ Binary stream writer provides methods to write a header followed by compressed GeoJSON Features  """

    __slots__ = ("stream",)
    GEOSTREAM_SCHEMA_VERSION: int

    def __init__(
        self, stream: typ.BinaryIO, props: typ.Optional[typ.Mapping[str, typ.Any]] = None, srid: int = GEOJSON_EPSG_SRID
    ) -> None:
        self.stream: typ.BinaryIO = stream
        self._write_header(srid, props)

    @abc.abstractmethod
    def _dump_properties(self, properties: Properties) -> typ.Optional[bytes]:
        ...

    @abc.abstractmethod
    def _dump_feature(self, feature: Feature) -> bytes:
        ...

    def _write_header(self, srid: int, props: typ.Optional[typ.Mapping[str, typ.Any]] = None) -> None:
        """ Only write the header if at the start of the stream - allowing appending to a stream in progress """
        if self.stream.tell() == 0:
            properties: typ.Optional[bytes] = self._dump_properties(props)
            props_len = len(properties) if properties else 0
            self.stream.write(struct.pack("Bii", self.GEOSTREAM_SCHEMA_VERSION, srid, props_len))
            if properties is not None:
                self.stream.write(properties)

    def write_feature(self, feature: typ.Union[typ.Mapping, Feature]) -> None:
        """ Write a geojson feature as a compressed GeoJSON feature """
        if not isinstance(feature, Feature):
            feature = Feature.from_dict(feature)
        zipped_data: bytes = self._dump_feature(feature)
        zip_len: int = len(zipped_data)
        self.stream.write(struct.pack("i", zip_len))
        self.stream.write(zipped_data)
        self.stream.write(struct.pack("i", zip_len))

    def write_feature_collection(self, collection: typ.Union[typ.Mapping, FeatureCollection]) -> None:
        """ Write all features from a geojson feature collection as compressed GeoJSON features """
        if not isinstance(collection, FeatureCollection):
            collection = FeatureCollection(**collection)
        for feature in collection.features:
            self.write_feature(feature)
