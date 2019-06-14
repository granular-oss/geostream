BUILD_NUMBER?=0

.PHONY: build bump_major bump_minor bump_patch clean dev lock package test


all:
	@echo 'Commands:'
	@echo ''
	@echo 'init - setup pipenv'
	@echo 'bump_major - bump the major version of the project'
	@echo 'bump_minor - bump the minor version of the project'
	@echo 'bump_patch - bump the patch version of the project'
	@echo 'clean - clean the build and test files'
	@echo 'dev - install the dev dependencies and start a pipenv shell'
	@echo 'lock - update the pipenv lock file'
	@echo 'package - build the pip package'
	@echo 'test - run the tests and linting'
	@echo 'test-ci - run the tests and linting'

init:
	pip install pipenv --upgrade
	pipenv install --dev

bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

bump_major:
	bumpversion major

black:
	black geostream/*

test:
	@echo "--------------------------------------------------------------------------------"
	@echo "running tests"
	@echo "--------------------------------------------------------------------------------"
	./run_tests.sh

test-ci:
	@echo "--------------------------------------------------------------------------------"
	@echo "running tests on ci server"
	@echo "--------------------------------------------------------------------------------"
	pipenv run ./run_tests.sh

dev:
	pipenv shell

lock:
	@echo "--------------------------------------------------------------------------------"
	@echo "updating pipenv lock file"
	@echo "--------------------------------------------------------------------------------"
	pipenv lock

package: build
	@echo "--------------------------------------------------------------------------------"
	@echo "building package"
	@echo "--------------------------------------------------------------------------------"
	pipenv run ./package.sh

clean:
	rm -rf build
	rm -rf dist
	rm -rf results
	rm -rf geostream.egg-info
