# geostream

This package contains:

* Module functions for reading and writing GeoStream data
* A command line utility that unpacks file(s) containing GeoStream data into GeoJSON file(s), each containing
a GeoJSON FeatureCollection.

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
`geostream` supports read and write of compressed GeoJSON Features on a binary stream, called GeoStream that supports
serialization and deserialization of arbitrary length collections of GeoJSON Features. Each GeoStream starts with
a header that is followed by any number of compressed GeoJSON Features. GeoStreams may be stored in files with a
nominal file extension of `.gjz`.

This package supplies:
* A reader object inputs from an already opened binary file-like object (stream)
  * provides properties to access header data read from the start of the stream
  * is an iterator that returns each GeoJSON Feature read from the stream, as an uncompressed geojson object
* A writer object outputs to an already opened binary file-like object (stream)
  * on initialization, writes out a header if the stream is at the beginning (offset 0)
  * writes compressed GeoJSON Features to the stream
* A command line utility, **unpack_gjz**, unpacks one or more GeoStream files into
json text files formatted as GeoJSON FeatureCollections
  * run `unpack_gjz -h` for detailed instructions
  * positional (required) arguments may be a single GeoStream file or multiple files, including file globs
  * the optional `-o OUT` argument may be a single `<path>.json` file only if the positional argument is a single
  geostream file, otherwise it is treated as a directory path, which is created if it doesn't exist
  * the optional `-s SELECT` argument matches GeoStream feature properties against the `SELECT` JSON formatted
  string, to unpack only selected features
  * Bash shell example: `unpack_gjz -v -o ./filtered -s {\"foo\":true} *.gjz` will unpack each `.gjz` file in
  the current directory, only extracting features with a property `foo` set to `true`, and then write the unpacked
  GeoJSON files to the `.filtered` sub-directory. The `-v` flag will print unpack progress and the number of
  extracted features for each file.

##  Module Contents <a name="modulecontents"></a>
The `geostream` module defines the following functions:
* geostream.**reader**(*stream, reverse=False*)<br>
Return a reader object which will read the header then iterate over the compressed Features in the *stream*.
*stream* can be any readable object that conforms to the BinaryIO type, such as the file-like object returned from
opening a GeoStream file with **'rb'** flags.\
\
The reader object provides the following properties for accessing GeoStream header data:
  * **schema_version** - an integer number that is the geostream schema version supported by this module
  * **srid** - an integer number that is the EPSG SRID of the coordinate reference system for the GeoJSON Feature
  geometry's x and y coordinates
    * The nominal and default GeoJSON SRID is for WGS-84.
    * Use of other SRID is not supported by the GeoJSON specification, but are not prohibited.
    Readers should check this property to verify they can properly handle the coordinate values.
  * **properties** - an optional dictionary of key/value properties that were provided by the writer.
    * Default is None<br>

  A short usage example for printing stream header data, then iterating forward through the stream:
  ```text
  >>> import geojson
  >>> from geostream import geostream
  >>> with open('compressed_data.gjz', 'rb') as stream:
  ...     georeader = geostream.reader(stream)
  ...     print(f"Coordinate SRID: {georeader.srid}")
  ...     print(f"Stream schema version: {georeader.schema_version}\n")
  ...     for feature in georeader:
  ...         print(f"{geojson.dumps(feature)}\n")
  ...
  Coordinate SRID: 4326
  Stream schema version: 3

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

  A short usage example for iterating in reverse (schema v3+ only), from the end of the stream:
  ```text
  >>> import geojson
  >>> from geostream import geostream
  >>> with open('compressed_data.gjz', 'rb') as stream:
  ...     georeader = geostream.reader(stream, reverse=True)
  ...     for feature in georeader:
  ...         print(f"{geojson.dumps(feature)}\n")
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
Return a writer object responsible for converting the user's GeoJSON Features into compressed data on the given
*stream*. *stream* can be any writeable object that conforms to the BinaryIO type, such as the file-like object
returned from opening a file with **'wb'** flags. *props* is an optional dictionary of arbitrary properties
that are converted to JSON and written to the stream header. *srid* is an optional override that should be
specified if the coordinate system of x, y data are not WGS-84. Reference [EPSG](http://www.epsg.org/) for
defined SRID values.\
\
The writer object provides the following methods for writing GeoJSON Features to the stream:
  * **write_feature**(*feature: geojson.Feature*) - compresses and writes the geojson Feature object to the stream
  * **write_feature_collection**(*collection: geojson.FeatureCollection*) - iterates over the geojson FeatureCollection,
  compressing and writing each Feature from the collection to the stream
  
  A short usage example:
  ```text
  >>> import geojson
  >>> from geostream import geostream
  >>> with open('compressed_data.gjz', 'wb') as stream:
  ...     geowriter = geostream.writer(stream)
  ...     feature = geojson.Feature(geometry=geojson.Point((-115.81, 37.24)), properties={"key": "123"})
  ...     geowriter.write_feature(feature)
  ```

The `geostream` module defines the following constants:
* geostream.GEOJSON_EPSG_SRID<br>
The EPSG SRID of the GeoJSON specification defined nominal coordinate reference (WGS-84)

* geostream.GEOSTREAM_SCHEMA_VERSIONS<br>
A tuple containing the GeoStream schema versions that are supported by the reader.

## GeoStream Format<a name="geostreamformat"></a>
The current GeoStream schema version is: **3**

The GeoStream starts with a Header followed by any number of Compressed Features. Formats are as follows:
* Header: starting at byte zero and containing (in order):
  * 1-byte unsigned integer: GeoStream schema version set by the writer
  * 4-byte integer: geostream EPSG SRID, which for our purpose will be WGS-84, so is the constant: 4326
  * 4-byte integer: length of the optional properties included in the header
  * (optional) n-bytes, n == above length: JSON properties included in the header - only present if above length is > 0
* Compressed Feature: the header is followed by compressed GeoJSON Features, each formatted as follows:
  * 4-byte integer: length of the compressed GeoJSON Feature string
  * n-bytes, n == above length: gzip compressed GeoJSON Feature string
  * 4-byte integer: length of the compressed GeoJSON Feature string

##  Development
Run `make` to see a list of what you can do with this package.

## Author(s)
* Donna Okazaki <donnaokazaki@granular.ag>
