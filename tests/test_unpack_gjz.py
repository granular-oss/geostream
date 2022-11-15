import os
import sys
import typing as typ
from unittest.mock import patch

import pytest

from geostream.cli.unpack_gjz import cli


# Only allow one test to write to the same directory as the input files, then delete it to test default output
def test_unpack_file(gjz_file_current_schema: typ.Tuple[str, str]) -> None:
    file_name = gjz_file_current_schema[0]
    expected_output = os.path.dirname(file_name) + "/" + gjz_file_current_schema[1]
    testargs = ["cli", file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)
        os.remove(expected_output)


def test_unpack_bigger_file(gjz_file_larger_v3: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_larger_v3[0]
    expected_output = test_output_dir + gjz_file_larger_v3[1]
    testargs = ["cli", file_name, "-o", test_output_dir]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_select_bigger_file(gjz_file_larger_v3: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_larger_v3[0]
    expected_output = test_output_dir + "big_selected.json"
    selection = '{"prop0":"val1"}'
    testargs = ["cli", "-s", selection, "-o", expected_output, file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_reverse_unpack_bigger_file(gjz_file_larger_v3: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_larger_v3[0]
    expected_output = test_output_dir + "rev_big_vector.json"
    testargs = ["cli", "-r", "-o", expected_output, file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_fail_reverse_unpack_v2_file(gjz_file_v2_schema: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_v2_schema[0]
    expected_output = test_output_dir + gjz_file_v2_schema[1]
    testargs = ["cli", "-r", "-o", expected_output, file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert not os.path.isfile(expected_output)


def test_unpack_file_all_flags(gjz_file_current_schema: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_current_schema[0]
    expected_output = test_output_dir + "allfiags.json"
    testargs = ["cli", "-r", "-p", "-o", expected_output, file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_to_dir(gjz_file_no_props_v3: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_no_props_v3[0]
    output_dir = test_output_dir
    expected_output = test_output_dir + gjz_file_no_props_v3[1]
    testargs = ["cli", "-v", "-o", output_dir, file_name]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isfile(expected_output)


def test_unpack_multiple(gjz_files_all_in_dir: typ.Tuple[str, str], test_output_dir: str) -> None:
    files_glob = gjz_files_all_in_dir[0]
    output_dir = test_output_dir + "all_out"
    testargs = ["cli", "-o", output_dir, files_glob]
    with patch.object(sys, "argv", testargs):
        cli()
        assert os.path.isdir(output_dir)


def test_unpack_help() -> None:
    testargs = ["cli"]

    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", testargs):
            cli()


def test_unpack_wrong_version_file(gjz_file_wrong_version: typ.Tuple[str, str]) -> None:
    file_name = gjz_file_wrong_version[0]
    unexpected_output = os.path.dirname(file_name) + "/testdata_wrongversion.json"
    testargs = ["cli", file_name]

    with patch.object(sys, "argv", testargs):
        cli()
        assert not os.path.isfile(unexpected_output)


def test_unpack_wrong_file_ext(gjz_file_wrong_ext: typ.Tuple[str, str]) -> None:
    file_name = gjz_file_wrong_ext[0]
    unexpected_output = os.path.dirname(file_name) + "/testdata_wrongext.json"
    testargs = ["cli", file_name]

    with patch.object(sys, "argv", testargs):
        cli()
        assert not os.path.isfile(unexpected_output)


def test_unpack_missing_file(gjz_nonexistent_file: typ.Tuple[str, str]) -> None:
    file_name = gjz_nonexistent_file[0]
    unexpected_output = gjz_nonexistent_file[1]
    testargs = ["cli", file_name]

    with patch.object(sys, "argv", testargs):
        cli()
        assert not os.path.isfile(unexpected_output)


def test_unpack_bad_out_dir(gjz_file_current_schema: typ.Tuple[str, str]) -> None:
    file_name = gjz_file_current_schema[0]
    expected_output = "/no_dir/file.gjz"
    testargs = ["cli", "-o", expected_output, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", testargs):
            cli()


def test_unpack_bad_out_param(gjz_files_all_in_dir: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_files_all_in_dir[0]
    bad_expected_output = test_output_dir + "filename.json"
    testargs = ["cli", "-o", bad_expected_output, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", testargs):
            cli()


def test_unpack_bad_out_param2(
    gjz_files_all_in_dir: typ.Tuple[str, str], gjz_file_wrong_ext: typ.Tuple[str, str]
) -> None:
    file_name = gjz_files_all_in_dir[0]
    bad_output_should_be_dir_is_file = gjz_file_wrong_ext[0]
    testargs = ["cli", "-o", bad_output_should_be_dir_is_file, file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", testargs):
            cli()


def test_unpack_bad_input(test_file_dir: str) -> None:
    bad_file_name_not_a_file = test_file_dir
    not_expected_output = test_file_dir + ".json"
    testargs = ["cli", bad_file_name_not_a_file]

    with patch.object(sys, "argv", testargs):
        cli()
        assert not os.path.isfile(not_expected_output)


def test_unpack_bad_select_param(gjz_file_current_schema: typ.Tuple[str, str], test_output_dir: str) -> None:
    file_name = gjz_file_current_schema[0]
    expected_output = test_output_dir + gjz_file_current_schema[1]
    testargs = ["cli", "-o", expected_output, "-s", "garbage-json", file_name]

    with pytest.raises(SystemExit):
        with patch.object(sys, "argv", testargs):
            cli()
