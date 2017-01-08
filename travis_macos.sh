#!/usr/bin/env bash

export ON_TRAVIS=false
export SKIP_DMG=false
export SKIP_SIGN=false
export SKIP_PYLINT=true

./packaging/scripts/travis/install_deps_macos.sh
./packaging/scripts/travis/run_tests.sh
./packaging/scripts/travis/run_pylint.sh
pip install .
./packaging/scripts/travis/build_macos.sh