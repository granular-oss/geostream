import pytest
import json
import io
import gzip
import struct

import geojson

from geostream import geostream


@pytest.mark.parametrize("gjson,props", [

    # should write point feature
    (geojson.Feature(geometry=geojson.Point((-115.81, 37.24)), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write multipoint feature
    (geojson.Feature(geometry=geojson.MultiPoint([(-155.52, 19.61), (-156.22, 20.74), (-157.97, 21.46)]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write linestring feature
    (geojson.Feature(geometry=geojson.LineString([(8.919, 44.4074), (8.923, 44.4075)]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write multilinestring feature
    (geojson.Feature(geometry=geojson.MultiLineString([[(3.75, 9.25), (-130.95, 1.52)], [(23.15, -34.25), (-1.35, -4.65), (3.45, 77.95)]]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write simple polygon feature
    (geojson.Feature(geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write polygon with holes feature
    (geojson.Feature(geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)], [(-5.21, 23.51), (15.21, -10.81), (-20.51, 1.51), (-5.21, 23.51)]]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

    # should write multipolygon feature
    (geojson.Feature(geometry=geojson.MultiPolygon([([(3.78, 9.28), (-130.91, 1.52), (35.12, 72.234), (3.78, 9.28)],), ([(23.18, -34.29), (-1.31, -4.61), (3.41, 77.91), (23.18, -34.29)],)]), properties={"prop0": "val0"}), {"unit": "something", "key": "uuid"}),

])
def test_write_read_geojson_with_props(gjson, props):
    byte_stream = io.BytesIO()
    writer = geostream.writer(byte_stream, props)
    writer.write_feature(gjson)
    byte_stream.seek(0)
    header1, header2, prop_len = struct.unpack('Bii', byte_stream.read(struct.calcsize('Bii')))
    assert header1 in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert header2 == geostream.GEOJSON_EPSG_SRID
    assert prop_len > 0
    prop_data = byte_stream.read(prop_len)
    prop_dict = json.loads(prop_data)
    assert len(prop_data) == prop_len
    assert type(prop_dict) == dict
    assert prop_dict["unit"] == "something"
    length = struct.unpack('i', byte_stream.read(struct.calcsize('i')))[0]
    zipped_data = byte_stream.read(length)
    trailing_length = struct.unpack('i', byte_stream.read(struct.calcsize('i')))[0]
    assert len(zipped_data) == length
    assert length == trailing_length
    byte_stream.seek(0)
    reader = geostream.reader(byte_stream)
    assert reader.srid == geostream.GEOJSON_EPSG_SRID
    assert reader.schema_version in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert reader.properties == props
    read_features = [f for f in reader]
    assert len(read_features) == 1
    assert gjson == read_features[0]
    byte_stream.seek(0)
    rev_reader = geostream.reader(byte_stream, reverse=True)
    assert rev_reader.srid == geostream.GEOJSON_EPSG_SRID
    assert rev_reader.schema_version in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert rev_reader.properties == props
    rev_features = [f for f in rev_reader]
    assert len(rev_features) == 1
    assert gjson == read_features[0]


def test_write_geojson_feature_collection_no_props():
    feature_list = [geojson.Feature(geometry=geojson.Polygon([[(10, 10), (40, 10), (40, 40), (10, 40), (10, 10)], [(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)]]), properties={"prop0": "val0"})]
    collection = geojson.FeatureCollection(feature_list)
    expected_out = '{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[10,10],[40,10],[40,40],[10,40],[10,10]],[[20,20],[30,20],[30,30],[20,30],[20,20]]]},"properties":{"prop0":"val0"}}'
    output_stream = io.BytesIO()
    writer = geostream.writer(output_stream, {})
    writer.write_feature_collection(collection)
    output_stream.seek(0)
    header1, header2, props_len = struct.unpack('Bii', output_stream.read(struct.calcsize('Bii')))
    assert header1 in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert header2 == geostream.GEOJSON_EPSG_SRID
    assert props_len == 0
    length = struct.unpack('i', output_stream.read(struct.calcsize('i')))[0]
    zipped_data = output_stream.read(length)
    trailing_length = struct.unpack('i', output_stream.read(struct.calcsize('i')))[0]
    assert len(zipped_data) == length
    assert length == trailing_length
    gjson = gzip.decompress(zipped_data)
    assert geojson.loads(gjson) == geojson.loads(expected_out)


def test_write_geojson_feature_collection_diff_srid():
    feature_list = [geojson.Feature(geometry=geojson.Polygon([[(10, 10), (40, 10), (40, 40), (10, 40), (10, 10)], [(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)]]), properties={"prop0": "val0"})]
    collection = geojson.FeatureCollection(feature_list)
    expected_out = '{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[10,10],[40,10],[40,40],[10,40],[10,10]],[[20,20],[30,20],[30,30],[20,30],[20,20]]]},"properties":{"prop0":"val0"}}'
    output_stream = io.BytesIO()
    writer = geostream.writer(output_stream, srid=1234)
    writer.write_feature_collection(collection)
    output_stream.seek(0)
    header1, header2, props_len = struct.unpack('Bii', output_stream.read(struct.calcsize('Bii')))
    assert header1 in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert header2 == 1234
    assert props_len == 0
    length = struct.unpack('i', output_stream.read(struct.calcsize('i')))[0]
    zipped_data = output_stream.read(length)
    trailing_length = struct.unpack('i', output_stream.read(struct.calcsize('i')))[0]
    assert len(zipped_data) == length
    assert length == trailing_length
    gjson = gzip.decompress(zipped_data)
    assert geojson.loads(gjson) == geojson.loads(expected_out)


def test_read_gjson_features_from_longer_stream():
    feature_list = [
        geojson.Feature(geometry=geojson.Polygon([[(10, 10), (40, 10), (40, 40), (10, 40), (10, 10)], [(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)]]), properties={"prop0": "val0"}),
        geojson.Feature(geometry=geojson.Polygon([[(41, 41), (50, 11), (50, 50), (41, 50), (41, 41)]]), properties={"prop0": "val1"}),
        geojson.Feature(geometry=geojson.Polygon([[(50, 50), (60, 50), (60, 60), (50, 60), (50, 50)]]), properties={"prop0": "val2"}),
    ]
    collection = geojson.FeatureCollection(feature_list)
    collection_props = {"unit": "something", "key": "uuid"}
    byte_stream = io.BytesIO()
    writer = geostream.writer(byte_stream, collection_props)
    for i in range(0,100):
        writer.write_feature_collection(collection)
    byte_stream.seek(0)
    reader = geostream.reader(byte_stream)
    assert reader.srid == geostream.GEOJSON_EPSG_SRID
    assert reader.schema_version in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert reader.properties == collection_props
    read_features = [f for f in reader]
    assert len(read_features) == 300
    assert feature_list[0] == read_features[0]
    assert feature_list[1] == read_features[1]
    assert feature_list[2] == read_features[2]


def test_reverse_read_gjson_features_from_longer_stream():
    feature_list = [
        geojson.Feature(geometry=geojson.Polygon([[(10, 10), (40, 10), (40, 40), (10, 40), (10, 10)], [(20, 20), (30, 20), (30, 30), (20, 30), (20, 20)]]), properties={"prop0": "val0"}),
        geojson.Feature(geometry=geojson.Polygon([[(41, 41), (50, 11), (50, 50), (41, 50), (41, 41)]]), properties={"prop0": "val1"}),
        geojson.Feature(geometry=geojson.Polygon([[(50, 50), (60, 50), (60, 60), (50, 60), (50, 50)]]), properties={"prop0": "val2"}),
    ]
    collection = geojson.FeatureCollection(feature_list)
    collection_props = {"unit": "something", "key": "uuid"}
    byte_stream = io.BytesIO()
    writer = geostream.writer(byte_stream, collection_props)
    for i in range(0,100):
        writer.write_feature_collection(collection)
    byte_stream.seek(0)
    reader = geostream.reader(byte_stream, reverse=True)
    assert reader.srid == geostream.GEOJSON_EPSG_SRID
    assert reader.schema_version in geostream.GEOSTREAM_SCHEMA_VERSIONS
    assert reader.properties == collection_props
    read_features = [f for f in reader]
    assert len(read_features) == 300
    assert feature_list[0] == read_features[2]
    assert feature_list[1] == read_features[1]
    assert feature_list[2] == read_features[0]


def test_read_truncated_after_feature_length():
    feature_list = [
        geojson.Feature(geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]]), properties={"prop0": "val0"}),
    ]
    collection = geojson.FeatureCollection(feature_list)
    collection_props = {}
    byte_stream = io.BytesIO()
    writer = geostream.writer(byte_stream, collection_props)
    writer.write_feature_collection(collection)
    byte_stream.write(struct.pack("i", 2))  # append the length of a second feature, but don't append data
    byte_stream.seek(0)
    reader = geostream.reader(byte_stream)
    read_features = [f for f in reader]
    assert len(read_features) == 1


def test_read_truncated_feature_data():
    feature_list = [
        geojson.Feature(geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]]), properties={"prop0": "val0"}),
    ]
    collection = geojson.FeatureCollection(feature_list)
    byte_stream = io.BytesIO()
    writer = geostream.writer(byte_stream)
    writer.write_feature_collection(collection)
    byte_stream.seek(0)
    good_data = byte_stream.read()
    bad_byte_stream = io.BytesIO()
    bad_byte_stream.write(good_data[:-5])  # truncate trailing length and 1 byte of feature data
    bad_byte_stream.seek(0)
    reader = geostream.reader(bad_byte_stream)
    read_features = [f for f in reader]
    assert len(read_features) == 0


def test_read_empty_stream_raises_exception():
    with pytest.raises(struct.error):
        byte_stream = io.BytesIO()
        geostream.reader(byte_stream)


def test_reverse_read_empty_stream_raises_exception():
    with pytest.raises(struct.error):
        byte_stream = io.BytesIO()
        geostream.reader(byte_stream, reverse=True)


def test_read_invalid_schema_from_stream_raises_exception():
    with pytest.raises(ValueError):
        feature_list = [
            geojson.Feature(
                geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]]),
                properties={"prop0": "val0"}),
        ]
        collection = geojson.FeatureCollection(feature_list)
        collection_props = {"unit": "something", "key": "uuid"}
        byte_stream = io.BytesIO()
        writer = geostream.writer(byte_stream, collection_props)
        writer.write_feature_collection(collection)
        byte_stream.seek(0)
        byte_stream.write(struct.pack("B", 0))
        byte_stream.seek(0)
        geostream.reader(byte_stream)


def test_reverse_read_invalid_schema_from_stream_raises_exception():
    with pytest.raises(ValueError):
        feature_list = [
            geojson.Feature(
                geometry=geojson.Polygon([[(2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)]]),
                properties={"prop0": "val0"}),
        ]
        collection = geojson.FeatureCollection(feature_list)
        collection_props = {"unit": "something", "key": "uuid"}
        byte_stream = io.BytesIO()
        writer = geostream.writer(byte_stream, collection_props)
        writer.write_feature_collection(collection)
        byte_stream.seek(0)
        byte_stream.write(struct.pack("B", 0))
        byte_stream.seek(0)
        geostream.reader(byte_stream, reverse=True)
