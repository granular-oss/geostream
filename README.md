# geostream

This package contains:

* Module functions for reading and writing GeoStream headers and losslessly compressed GeoJSON-like Features
on a binary stream
* A command line utility that unpacks GeoStream file(s) into GeoJSON FeatureCollection file(s)

GeoJSON-like Features are GeoJSON formatted dictionaries, following the same JSON schema as GeoJSON Features
(ref: [GeoJSON](https://geojson.org)), with the following extension:
* Feature `properties` may contain simple objects with value types in that require custom JSON encoder/decoder
functions to dump/load JSON formatted strings.
* Supported value types are listed in the
[CBOR2](https://cbor2.readthedocs.io/en/latest/usage.html) documentation.

### Table of Contents

* [Installation](#installation)
* [Overview](#overview)
* [Module Contents](#modulecontents)
* [GeoStream Format](#geostreamformat)

## Installation <a name="installation"></a>
The recommended way to install geostream is via pip:
```bash
pip install geostream
```

## Overview <a name="overview"></a>
`geostream` supports read and write of compressed GeoStream Features on a binary stream, called GeoStream. This
supports serialization and deserialization of arbitrary length collections of GeoStream Features. Each GeoStream
starts with a header that is followed by any number of compressed GeoStream Features. GeoStreams should be stored
in files with a file extension of `.gjz`.

This package supplies:
* A reader object inputs from an already opened binary file-like object (stream)
  * provides properties to access header data read from the start of the stream
  * is an iterator that returns each GeoStream Feature read from the stream, as an uncompressed geojson object
* A writer object outputs to an already opened binary file-like object (stream)
  * on initialization, writes out a header if the stream is at the beginning (offset 0)
  * writes compressed GeoStream Features to the stream
* A command line utility, **unpack_gjz**, unpacks one or more GeoStream files into
json text files formatted as GeoJSON FeatureCollections. It includes a custom JSON encoder to support date/datetime
and UUID values in Feature properties and in the GeoStream header. GeoStream header properties are encoded as
GeoJSON FeatureCollection foreign members, named: `properties` and `crs`.
  * run `unpack_gjz -h` for detailed instructions
  * positional (required) arguments may be a single GeoStream file or multiple files, including file globs
  * the optional `-o OUT` argument may be a single `<path>.json` file only if the positional argument is a single
  geostream file, otherwise it is treated as a directory path, which is created if it doesn't exist
  * the optional `-s SELECT` argument matches GeoStream feature properties against the `SELECT` JSON formatted
  string, to unpack only selected features
  * Bash shell example: `unpack_gjz -v -o ./filtered -s {\"foo\":true} *.gjz` will unpack each `.gjz` file in
  the current directory, only extracting features with a property `foo` set to `true`, and then write the unpacked
  files to the `./filtered` sub-directory. The `-v` flag will print unpack progress and the number of
  extracted features for each file.

##  Module Contents <a name="modulecontents"></a>
The `geostream` module defines the following functions:
* geostream.**reader**(*stream, reverse=False*)<br>
Return a reader object which will read the header then iterate over the compressed Features in the *stream*.
*stream* can be any readable object that conforms to the BinaryIO type, such as the file-like object returned from
opening a GeoStream file with **'rb'** flags. Readers can read schema versions 3 and 4.\
\
The reader object provides the following properties for accessing GeoStream header data:
  * **schema_version** - an integer number that is the geostream schema version supported by this module
  * **srid** - an integer number that is the EPSG SRID of the coordinate reference system for the GeoJSON Feature
  geometry's x and y coordinates
    * The nominal and default GeoJSON SRID is for WGS-84.
    * Use of other SRID is not supported by the GeoJSON specification, but are not prohibited.
    Readers should check this property to verify they can properly handle the coordinate values.
  * **properties** - an optional dictionary of key/value properties that were provided by the writer.
    * Default is None.
    * As of schema version 4, the dictionary may include values listed in the
    [CBOR2](https://cbor2.readthedocs.io/en/latest/usage.html) documentation, such as datetime and UUID.
    The geostream writer and readers can handle these value types transparently, but formatting the read data as
    valid JSON requires a custom JSON encoder.<br>

  A short usage example for printing stream header data, then iterating forward through the stream,
  printing each feature in JSON format.
  ```text
  >>> import json
  >>> import geostream
  >>> with open('compressed_data.gjz', 'rb') as stream:
  ...     georeader = geostream.reader(stream)
  ...     print(f"Coordinate SRID: {georeader.srid}")
  ...     print(f"Stream schema version: {georeader.schema_version}\n")
  ...     for feature in georeader:
  ...         print(f"{json.dumps(feature, default=_datetime_to_json)}\n")
  ...
  Coordinate SRID: 4326
  Stream schema version: 4

  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[41, 41], [50, 11], [50, 50], [41, 50], [41, 41]]]
   },
   "properties": {"prop0": "val1"}}
 
  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[50, 50], [60, 50], [60, 60], [50, 60], [50, 50]]]},
   "properties": {"prop0": "val2"}}
  ```

  A short usage example for iterating forward through the stream, using a custom JSON encoder for datetime objects
  stored in the Feature properties.
  ```text
  >>> import json
  >>> import geostream
  >>> def _datetime_to_json(obj):
  ...     if isinstance(obj, (datetime, date)):
  ...        return obj.isoformat()
  ...     raise TypeError(repr(obj) + " is not JSON serializable")
  >>> with open('compressed_data.gjz', 'rb') as stream:
  ...     georeader = geostream.reader(stream)
  ...     for feature in georeader:
  ...         print(f"{json.dumps(feature, default=_datetime_to_json)}\n")
  ...
  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[41, 41], [50, 11], [50, 50], [41, 50], [41, 41]]]
   },
   "properties": {"timestamp": "2019-09-25 16:04:03.759568+00:00"}}
 
  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[50, 50], [60, 50], [60, 60], [50, 60], [50, 50]]]},
   "properties": {"timestamp": "2019-09-25 16:04:04.512457+00:00"}}
  ```

  A short usage example for iterating in reverse, from the end of the stream:
  ```text
  >>> import json
  >>> import geostream
  >>> with open('compressed_data.gjz', 'rb') as stream:
  ...     georeader = geostream.reader(stream, reverse=True)
  ...     for feature in georeader:
  ...         print(f"{json.dumps(feature)}\n")
  ...
  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[50, 50], [60, 50], [60, 60], [50, 60], [50, 50]]]},
   "properties": {"prop0": "val2"}}
 
  {"type": "Feature",
   "geometry": {
     "type": "Polygon",
     "coordinates": [[[41, 41], [50, 11], [50, 50], [41, 50], [41, 41]]]
   },
   "properties": {"prop0": "val1"}}
  ```

* geostream.**writer**(*stream*, *props=None*, *srid=geostream.GEOJSON_EPSG_SRID*)<br>
Return a writer object responsible for converting the user's GeoJSON-like Features into compressed data on the given
*stream*. *stream* can be any writeable object that conforms to the BinaryIO type, such as the file-like object
returned from opening a file with **'wb'** flags. *props* is an optional dictionary of arbitrary properties
that are written to the stream header. *srid* is an optional override that should be
specified if the coordinate system of x, y data are not WGS-84. Reference [EPSG](http://www.epsg.org/) for
defined SRID values.\
\
The writer object provides the following methods for writing Features to the stream:
  * **write_feature**(*feature: Feature*) - compresses and writes the Feature (or compliant dictionary) to the stream
  * **write_feature_collection**(*collection: FeatureCollection*) - iterates over a FeatureCollection,
  compressing and writing each Feature from the collection to the stream
  
  A short usage example adding feature properties containing CBOR2 compliant data types
  to the stream:
  ```text
  >>> import uuid
  >>> from datetime import datetime, timezone
  >>> import geostream
  >>> with open('compressed_data.gjz', 'wb') as stream:
  ...     header_props = dict(name="example", timestamp=datetime.now(tz=timezone.utc))
  ...     geowriter = geostream.writer(stream, props=header_props)
  ...     geojson_point = dict(type="Point", coordinates=[-115.81, 37.24])
  ...     props = dict(id = uuid.uuid4(), timestamp=datetime.now(tz=timezone.utc))
  ...     feature = geostream.Feature(geometry=geojson_point, properties=props)
  ...     geowriter.write_feature(feature)
  ```

The `geostream` module defines the following class:
* geostream.**Feature**<br>
This dictionary subclass provides a wrapper for geometry and properties to write to a geostream,
and is the object returned by geostream reader iterators.\
\
The following properties provide convenient access to Feature attributes:
  * **geometry**: returns the GeoJSON Feature's "geometry" value
  * **properties**: returns the GeoJSON Feature's "properties" value
  * **srid**: if defined, returns the [EPSG](http://www.epsg.org/) SRID, or None
  * **wkb**: return **geometry** converted to WKB format
  * **wkt**: return **geometry** converted to WKT format
  * **ewkb**: return **geometry** converted to EWKB format
  * **ewkt**: return **geometry** converted to EWKT format

The `geostream` module defines the following constants:
* geostream.GEOJSON_EPSG_SRID<br>
The EPSG SRID of the GeoJSON specification defined nominal coordinate reference (WGS-84)

* geostream.GEOSTREAM_SCHEMA_VERSIONS<br>
A tuple containing the GeoStream schema versions that are supported by the reader.

## GeoStream Format<a name="geostreamformat"></a>
The current GeoStream schema version is: **4**

The GeoStream starts with a Header followed by any number of Compressed Features. Formats are as follows:
* Header: starting at byte zero and containing (in order):
  * 1-byte unsigned integer: GeoStream schema version set by the writer
  * 4-byte integer: geostream EPSG SRID, which defaults to WGS-84, or SRID: 4326
  * 4-byte integer: length of the optional properties included in the header
  * (optional) n-bytes, n == above length: JSON-like dictionary containing string keys and CBOR supported values,
  only present if above length is > 0
    * New in schema version 4: properties may contain values with
    [CBOR2](https://cbor2.readthedocs.io/en/latest/usage.html) supported data types
* Compressed Feature: the header is followed by compressed GeoStream Features, each formatted as follows:
  * 4-byte integer: length of the compressed GeoStream Feature binary string
  * n-bytes, n == above length: zlib compressed GeoStream Feature binary string
  * 4-byte integer: length of the compressed GeoStream Feature binary string

##  Development
Run `make` to see a list of what you can do with this package.

## Author(s)
* Donna Okazaki <donnaokazaki@granular.ag>
* Eric Jensen <ericjensen@granular.ag>

## License
Proprietary, (c) 2019 Granular
