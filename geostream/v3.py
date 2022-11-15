import gzip
import typing as typ

import simplejson as json

from geostream.base import Feature, GeoStreamReader, GeoStreamReverseReader, GeoStreamWriter, Properties


class GeoStreamReaderV3(GeoStreamReader):
    """Stream header accessors and iterator over a readable binary stream of compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION = 3

    def _load_properties(self, buffer: bytes) -> Properties:
        return json.loads(buffer)

    def _load_feature(self, data: bytes) -> Feature:
        return self._construct_feature(json.loads(gzip.decompress(data).decode()))


class GeoStreamReverseReaderV3(GeoStreamReverseReader):
    """Stream header accessors and backwards iterator over a readable binary stream of compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION = 3

    def _load_properties(self, buffer: bytes) -> Properties:
        return json.loads(buffer)

    def _load_feature(self, data: bytes) -> Feature:
        return self._construct_feature(json.loads(gzip.decompress(data).decode()))


class GeoStreamWriterV3(GeoStreamWriter):
    """Binary stream writer provides methods to write a header followed by compressed GeoJSON Features"""

    GEOSTREAM_SCHEMA_VERSION: int = 3

    def _dump_properties(self, properties: Properties) -> typ.Optional[bytes]:
        if properties is not None:
            return json.dumps(properties).encode()
        else:
            return None

    def _dump_feature(self, feature: Feature) -> bytes:
        feature.wkb  # Validity check
        return gzip.compress(json.dumps(feature).encode())
