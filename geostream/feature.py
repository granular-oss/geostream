import typing as typ
from collections import ChainMap
from functools import lru_cache

from geomet import wkb, wkt

from geostream.constants import GEOJSON_EPSG_SRID

Geometry = typ.Mapping[str, typ.Any]
Properties = typ.Optional[typ.Mapping[str, typ.Any]]
CLS = typ.TypeVar("CLS", bound="Feature")


@lru_cache()
def srid_to_crs(srid: typ.Optional[int]) -> typ.Mapping:
    if srid is None:
        srid = GEOJSON_EPSG_SRID
    return {"type": "name", "properties": {"name": f"EPSG:{srid}"}}


@lru_cache()
def cached_crs(srid: typ.Optional[int]) -> typ.Mapping:
    if srid is None:
        srid = GEOJSON_EPSG_SRID
    return dict(crs=srid_to_crs(srid), meta={"srid": srid})


class Feature(dict, typ.MutableMapping[str, typ.Any]):
    """
    Light-weight GeoJSON Feature object.
    """

    def __init__(
        self, geometry: Geometry, properties: Properties = None, *, srid: typ.Optional[int] = None, **kwargs: typ.Any
    ) -> None:
        kwargs.pop("type", None)
        if properties is None:
            properties = {}
        if "crs" in kwargs:
            raise NotImplementedError("Feature does not support setting crs currently")
        super().__init__(geometry=geometry, properties=properties, type="Feature", **kwargs)
        self.__srid = srid

    @property
    def geometry(self) -> Geometry:
        return self["geometry"]

    @property
    def properties(self) -> Properties:
        return self["properties"]

    @property
    def srid(self) -> typ.Optional[int]:
        return self.__srid

    @property
    def wkb(self):
        return wkb.dumps(self["geometry"])

    @property
    def wkt(self):
        return wkt.dumps(self["geometry"])

    @property
    def ewkt(self):
        return wkt.dumps(ChainMap(cached_crs(self.__srid), self["geometry"]))

    @property
    def ewkb(self):
        return wkb.dumps(ChainMap(cached_crs(self.__srid), self["geometry"]))

    @classmethod
    def from_dict(cls: typ.Type[CLS], value: typ.Mapping, *, srid: typ.Optional[int] = None) -> CLS:
        return cls(srid=srid, **value)


class FeatureCollection(dict, typ.MutableMapping[str, typ.Any]):
    """
    Light-weight GeoJSON Feature object.
    """

    def __init__(
        self,
        features: typ.Sequence[Feature],
        properties: Properties = None,
        *,
        srid: int = GEOJSON_EPSG_SRID,
        **kwargs: typ.Any,
    ) -> None:
        kwargs.pop("type", None)
        if properties is not None:
            kwargs["properties"] = properties

        kwargs.setdefault("crs", srid_to_crs(srid))
        super().__init__(features=features, type="FeatureCollection", **kwargs)
        self.__srid = srid

    @property
    def features(self) -> typ.Sequence[Feature]:
        return self["features"]

    @property
    def properties(self) -> Properties:
        return self.get("properties")

    @property
    def srid(self) -> int:
        return self.__srid
