import os
import typing as typ
from datetime import datetime, timezone

import pytest

DOCKER_TEST_DIR = os.path.dirname(__file__)
DOCKER_TEST_FILES_DIR = DOCKER_TEST_DIR + "/test_files/"
DOCKER_TEST_OUT_DIR = DOCKER_TEST_DIR + "/_cli_out/"


def _make_feature(geom: dict, prop: dict) -> dict:
    return dict(type="Feature", geometry=geom, properties=prop)


def _get_test_file(gjz_file: str) -> typ.Tuple[str, str]:
    file_path = DOCKER_TEST_FILES_DIR + gjz_file
    _, name = os.path.split(file_path)
    base_name, _ = os.path.splitext(name)
    output_json_name = base_name + ".json"
    return file_path, output_json_name


@pytest.fixture(scope="function")
def feat_collection_1() -> dict:
    feature_list = [
        _make_feature(
            geom=dict(
                type="Polygon",
                coordinates=[
                    [[10, 10], [40, 10], [40, 40], [10, 40], [10, 10]],
                    [[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]],
                ],
            ),
            prop={"prop0": "val0"},
        )
    ]
    return dict(type="FeatureCollection", features=feature_list)


@pytest.fixture(scope="function")
def feat_collection_2() -> dict:
    feature_list = [
        _make_feature(
            geom=dict(
                type="Polygon",
                coordinates=[
                    [
                        [2.3812345673812914, 57.32238290582347],
                        [23.194, -20.28],
                        [-120.43, 19.15],
                        [2.3812345673812914, 57.32238290582347],
                    ]
                ],
            ),
            prop={"prop0": "val0"},
        )
    ]
    return dict(type="FeatureCollection", features=feature_list)


@pytest.fixture(scope="function")
def feat_collection_3() -> dict:
    feature_list = [
        _make_feature(
            geom=dict(
                type="Polygon",
                coordinates=[
                    [
                        [10.35126458923567, 10.35126458923569],
                        [40, 10],
                        [40, 40],
                        [10, 40],
                        [10.35126458923567, 10.35126458923569],
                    ],
                    [[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]],
                ],
            ),
            prop={"prop0": "val0"},
        ),
        _make_feature(
            geom=dict(type="Polygon", coordinates=[[[41, 41], [50, 11], [50, 50], [41, 50], [41, 41]]]),
            prop={"prop0": "val0"},
        ),
        _make_feature(
            geom=dict(type="Polygon", coordinates=[[[50, 50], [60, 50], [60, 60], [50, 60], [50, 50]]]),
            prop={"prop0": "val0"},
        ),
    ]
    return dict(type="FeatureCollection", features=feature_list)


@pytest.fixture(scope="function")
def test_timestamp() -> datetime:
    return datetime(2019, 9, 25, 16, 4, 3, 759568, tzinfo=timezone.utc)


@pytest.fixture(scope="function")
def gjz_file_current_schema() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_schema_v4.gjz")


@pytest.fixture(scope="function")
def gjz_file_v2_schema() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_schema_v2.gjz")


@pytest.fixture(scope="function")
def gjz_file_v3_schema() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_schema_v3.gjz")


@pytest.fixture(scope="function")
def gjz_file_larger_v3() -> typ.Tuple[str, str]:
    return _get_test_file("big_vector_v3.gjz")


@pytest.fixture(scope="function")
def gjz_file_no_props_v3() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_noprops_v3.gjz")


@pytest.fixture(scope="function")
def gjz_files_all_in_dir() -> typ.Tuple[str, str]:
    file_dir = DOCKER_TEST_FILES_DIR
    file_path = file_dir + "/*.gjz"
    return file_path, file_dir


@pytest.fixture(scope="function")
def gjz_nonexistent_file() -> typ.Tuple[str, str]:
    return _get_test_file("nonexistent.gjz")


@pytest.fixture(scope="function")
def gjz_file_wrong_ext() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_wrongext.csv")


@pytest.fixture(scope="function")
def gjz_file_wrong_version() -> typ.Tuple[str, str]:
    return _get_test_file("testdata_wrongversion.gjz")


@pytest.fixture(scope="function")
def test_file_dir() -> str:
    return DOCKER_TEST_DIR + "/test_files"


@pytest.fixture(scope="function")
def test_output_dir() -> str:
    return DOCKER_TEST_OUT_DIR
