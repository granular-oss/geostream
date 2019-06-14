import pytest
import sys
import os
from unittest.mock import patch

from geostream.cli.unpack_gjz import cli

APP_DIR = os.path.abspath(os.path.split(os.path.split(__file__)[0])[0])


def test_unpack_file():
    file_name = APP_DIR + "/tests/test_files/testdata.gjz"
    root, _ = os.path.splitext(file_name)
    expected_output = root + ".json"
    testargs = ["cli", file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_bigger_file():
    file_name = APP_DIR + "/tests/test_files/big_vector.gjz"
    root, _ = os.path.splitext(file_name)
    expected_output = root + ".json"
    testargs = ["cli", file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_select_bigger_file():
    file_name = APP_DIR + "/tests/test_files/big_vector.gjz"
    root, _ = os.path.splitext(file_name)
    expected_output = os.path.dirname(file_name) + "/big_selected.json"
    selection = "{\"prop0\":\"val1\"}"
    testargs = ["cli", "-s", selection, "-o", expected_output, file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_reverse_unpack_bigger_file():
    file_name = APP_DIR + "/tests/test_files/big_vector.gjz"
    expected_output = os.path.dirname(file_name) + "/rev_big_vector.json"
    testargs = ["cli", "-r", "-o", expected_output, file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_fail_reverse_unpack_v2_file():
    file_name = APP_DIR + "/tests/test_files/testdata_schema_v2.gjz"
    expected_output = os.path.dirname(file_name) + "/rev_testdata_schema_v2.json"
    testargs = ["cli", "-r", "-o", expected_output, file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_file_all_flags():
    file_name = APP_DIR + "/tests/test_files/testdata.gjz"
    expected_output = os.path.dirname(file_name) + "/allfiags.json"
    testargs = ["cli", "-r", "-p", "-o", expected_output, file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_to_dir():
    file_name = APP_DIR + "/tests/test_files/testdata_noprops.gjz"
    output_dir = os.path.dirname(file_name)
    root, _ = os.path.splitext(file_name)
    expected_output = root + ".json"
    testargs = ["cli", "-v", "-o", output_dir, file_name]
    with patch.object(sys, 'argv', testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_upack_help():
    testargs = ["cli"]

    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', testargs):
            cli()


def test_unpack_wrong_version_file():
    file_name = APP_DIR + "/tests/test_files/testdata_wrongversion.gjz"
    expected_output = os.path.dirname(file_name) + "/testdata_wrongversion.json"
    testargs = ["cli", file_name]

    with patch.object(sys, 'argv', testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_wrong_file_ext():
    file_name = APP_DIR + "/tests/test_files/testdata_wrongext.csv"
    expected_output = os.path.dirname(file_name) + "/testdata_wrongext.json"
    testargs = ["cli", file_name]

    with patch.object(sys, 'argv', testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_missing_file():
    file_name = APP_DIR + "/tests/test_files/testdata_missing.gjz"
    expected_output = os.path.dirname(file_name) + "/testdata_missing.json"
    testargs = ["cli", file_name]

    with patch.object(sys, 'argv', testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_bad_out_dir():
    file_name = APP_DIR + "/tests/test_files/testdata.gjz"
    expected_output = "/no_dir/file.gjz"
    testargs = ["cli", "-o", expected_output, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', testargs):
            cli()


def test_unpack_bad_out_param():
    file_name = APP_DIR + "/tests/test_files/*.gjz"
    expected_output = APP_DIR + "/tests/test_files/file.json"
    testargs = ["cli", "-o", expected_output, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', testargs):
            cli()


def test_unpack_bad_out_param2():
    file_name = APP_DIR + "/tests/test_files/*.gjz"
    expected_output = APP_DIR + "/tests/test_files/testdata_wrongext.csv"
    testargs = ["cli", "-o", expected_output, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', testargs):
            cli()


def test_unpack_bad_input():
    file_name = APP_DIR + "/tests/test_files"
    expected_output = APP_DIR + "/tests/test_files.json"
    testargs = ["cli", file_name]

    with patch.object(sys, 'argv', testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_bad_select_param():
    file_name = APP_DIR + "/tests/test_files/testdata.gjz"
    testargs = ["cli", "-s", "garbage-json", file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', testargs):
            cli()
