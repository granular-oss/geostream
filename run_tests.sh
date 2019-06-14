#!/bin/sh -e
dir="$( cd "$( dirname "$0" )" && pwd )"
cd $dir
. ./util.sh

mkdir -p results

logit 'running tests'
pytest $@
