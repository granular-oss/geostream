import io
import typing as typ

from geostream.constants import GEOJSON_EPSG_SRID
from geostream.base import GeoStreamReader, GeoStreamWriter, read_header
from geostream.v3 import GeoStreamReaderV3, GeoStreamReverseReaderV3
from geostream.v4 import GeoStreamReaderV4, GeoStreamReverseReaderV4, GeoStreamWriterV4


def reader(stream: typ.BinaryIO, reverse: bool = False, rev_buf_size: int = io.DEFAULT_BUFFER_SIZE) -> GeoStreamReader:
    """
    Return a geojson Feature iterator that reads and unpacks compressed GeoJSON features from the stream
    until the features are exhausted, and provides properties to access the unpacked header data
    :param stream: Readable Binary IO object
    :param reverse: Flag to reverse the order of iteration from the end of the stream. Default: False
    :param rev_buf_size: Buffer length for reverse iterator
    :return: GeoStreamReader object
    """
    header = read_header(stream)

    if header.version == 4:
        if reverse is False:
            return GeoStreamReaderV4(stream)
        else:
            return GeoStreamReverseReaderV4(stream, buf_size=rev_buf_size)
    else:
        if reverse is False:
            return GeoStreamReaderV3(stream)
        else:
            return GeoStreamReverseReaderV3(stream, buf_size=rev_buf_size)


def writer(
    stream: typ.BinaryIO, props: typ.Optional[typ.Mapping[str, typ.Any]] = None, srid: int = GEOJSON_EPSG_SRID
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
    return GeoStreamWriterV4(stream, props, srid=srid)
