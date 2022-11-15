#!/usr/bin/env python3

import argparse
import sys
import typing as typ
from collections import deque
from datetime import date, datetime
from functools import partial
from glob import iglob
from pathlib import Path
from uuid import UUID

import simplejson as json

import geostream
from geostream.feature import Feature, FeatureCollection

_feature_count = deque([0], maxlen=1)  # internal counter


def _cbor2types_to_json(obj: typ.Any) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    raise TypeError(repr(obj) + " is not JSON serializable")


def cli() -> None:
    args = parse_args()

    output_one_named_file = False
    output_path = None
    if args.out:
        output_path = Path(args.out)
        if output_path.suffix == ".json":
            if len(args.inputs) == 1 and Path(args.inputs[0]).is_file():
                output_one_named_file = True
            else:
                sys.stderr.write(f"Output path must be a directory for multiple input files, not: {args.out}\n")
                exit(1)
        elif not output_path.exists():
            try:
                output_path.mkdir(parents=True)
            except Exception as e:
                sys.stderr.write(f"Un-writeable output path: {args.out}. Error: {e}")
        elif not output_path.is_dir():
            sys.stderr.write(f"Existing output path must be a directory: {args.out}\n")
            exit(1)

    select = {}
    if args.select:
        try:
            select = json.loads(args.select)
        except Exception as e:
            sys.stderr.write(f"Invalid select text, must be valid JSON string: {args.select}. Error: {e}\n")
            exit(1)

    for gjz_file in [f for i in args.inputs for f in iglob(i)]:
        input_gjz = Path(gjz_file)

        if not input_gjz.is_file() or not input_gjz.exists():
            print(f"Skipped: {gjz_file}, which is not a file or does not exist")
            continue
        if input_gjz.suffix != ".gjz":
            print(f"Skipped: {gjz_file}, which does not have the name extension: .gjz")
            continue

        if output_one_named_file:
            output_file = output_path
        elif output_path is not None:
            output_file = output_path.joinpath(input_gjz.stem + ".json")
        else:
            output_file = input_gjz.parent.joinpath(input_gjz.stem + ".json")

        if args.verbose:
            print(f"Unpacking: {gjz_file} into: {output_file}")

        with input_gjz.open("rb") as bf:
            try:
                reader = geostream.reader(bf, reverse=args.reverse)
            except Exception as e:
                print(f"...failed to open {gjz_file}, error: {e}")
                continue

            if select:
                selected: typ.Iterable[Feature] = filter(
                    lambda feat: all(item in feat.properties.items() for item in select.items()), reader
                )
            else:
                selected = reader

            if args.verbose:
                _feature_count.append(0)
                selected = map(_count_features, selected)

            geojson_collection = FeatureCollection(
                features=tuple(selected), properties=reader.properties, srid=reader.srid
            )

            try:
                assert output_file is not None
                with output_file.open("w") as tf:
                    dump_fn = partial(
                        json.dump,
                        geojson_collection,
                        tf,
                        allow_nan=False,
                        iterable_as_array=True,
                        default=_cbor2types_to_json,
                    )
                    if args.pretty:
                        dump_fn(indent=4, sort_keys=True)
                    else:
                        dump_fn()
            except Exception as e:
                sys.stderr.write(f"...bad out directory path, failed to open: {output_file}, error: {e}")
                exit(1)

            if args.verbose:
                filtered = f"selected by: {select}" if select else "selected all"
                print(f"...unpacked {_feature_count[0]} Features, {filtered}")


def _count_features(pass_thru: typ.Any) -> typ.Any:
    _feature_count.appendleft(_feature_count.popleft() + 1)
    return pass_thru


def parse_args():  # type: ignore
    parser = argparse.ArgumentParser(description="Unpack one or more GeoStream compressed files to GeoJSON")
    parser.add_argument(
        "inputs", type=str, metavar="GJZ", nargs="+", help="path(s) to the input geostream (.gjz) file or files"
    )
    parser.add_argument("-r", "--reverse", action="store_true", help="reverse feature order in collection")
    parser.add_argument("-p", "--pretty", action="store_true", help="make the output JSON pretty")
    parser.add_argument("-v", "--verbose", action="store_true", help="print unpack information to console")
    parser.add_argument("-o", "--out", help="path to the GeoJSON output directory or .json file for single input file")
    parser.add_argument(
        "-s", "--select", help="JSON string to select Features with matching properties to write to output"
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()
