#!/bin/sh -e
dir="$( cd "$( dirname "$0" )" && pwd )"
echo $dir
cd $dir
. util.sh

mkdir -p dist

logit "replacing build number"
# get revision
BUILD_NUMBER=${BUILD_NUMBER:-0}
sed -Ei "s/__build__\s+=\s+[0-9]+/__build__ = ${BUILD_NUMBER}/g" setup.py


logit "packaging wheel"
# build the wheel
python setup.py bdist_wheel sdist
