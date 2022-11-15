import typing as typ
import zlib

import cbor2
from geomet import wkb

from geostream.base import Feature, GeoStreamReader, GeoStreamReverseReader, GeoStreamWriter, Properties


class GeoStreamReaderV4(GeoStreamReader):
    """Stream header accessors and iterator over a readable binary stream of compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION = 4

    def _load_properties(self, buffer: bytes) -> Properties:
        return cbor2.loads(buffer)

    def _load_feature(self, data: bytes) -> Feature:
        feature = cbor2.loads(zlib.decompress(data))
        feature["geometry"] = wkb.loads(feature["geometry"])
        return self._construct_feature(feature)


class GeoStreamReverseReaderV4(GeoStreamReverseReader):
    """Stream header accessors and backwards iterator over a readable binary stream of compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION = 4

    def _load_properties(self, buffer: bytes) -> Properties:
        return cbor2.loads(buffer)

    def _load_feature(self, data: bytes) -> Feature:
        feature = cbor2.loads(zlib.decompress(data))
        feature["geometry"] = wkb.loads(feature["geometry"])
        return self._construct_feature(feature)


class GeoStreamWriterV4(GeoStreamWriter):
    """Binary stream writer provides methods to write a header followed by compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION: int = 4

    def _dump_properties(self, properties: Properties) -> typ.Optional[bytes]:
        if properties is not None:
            return cbor2.dumps(properties)
        else:
            return None

    def _dump_feature(self, feature: Feature) -> bytes:
        result = dict(feature)
        result["geometry"] = feature.wkb
        return zlib.compress(cbor2.dumps(result))
