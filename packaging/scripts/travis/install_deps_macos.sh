#!/bin/sh

set -euo pipefail
set -o xtrace

if [ ${ON_TRAVIS} = true ]; then
    wget https://www.python.org/ftp/python/2.7.11/python-2.7.11-macosx10.6.pkg
    sudo installer -pkg python-2.7.11-macosx10.6.pkg -target /
    pip install -U pip
fi

brew update

# follow this pattern to avoid failing if its already
# installed by brew:
# http://stackoverflow.com/a/20802425
if brew ls --versions gmp > /dev/null; then
    echo 'gmp is already installed by brew'
else
    brew install gmp
fi

if brew ls --versions openssl > /dev/null; then
    echo 'openssl is already installed by brew'
else
    brew install openssl
    brew link --force openssl
fi

MODULES="pyobjc-core==3.1.1 pyobjc-framework-Cocoa==3.1.1 pyobjc-framework-CFNetwork==3.1.1 pyobjc-framework-Quartz==3.1.1"

if [ ${ON_TRAVIS} = true ]; then
    WHEEL_DIR="${TRAVIS_BUILD_DIR}/cache/wheel"
    mkdir -p "${WHEEL_DIR}"
    # mapping from the package name to the
    # actual built wheel file is surprisingly
    # hard so instead of checking for the existance
    # of each wheel, we mark with a file when they've all been
    # built and skip when that file exists
    for MODULE in ${MODULES}; do
	if [ ! -f "${WHEEL_DIR}"/${MODULE}.finished ]; then
	    pip wheel -w "${WHEEL_DIR}" ${MODULE}
	    touch "${WHEEL_DIR}"/${MODULE}.finished
	    pip install ${MODULE}
	fi
    done
fi

pip install $MODULES
pip install pyobjc==3.1.1
pip install setuptools==19.2 --upgrade

if [ ! -d "py2app" ]; then
   hg clone https://bitbucket.org/ronaldoussoren/py2app
   cd py2app
   hg checkout py2app-0.10
   # this commit fixes a bug that should have been fixed as part of 0.10
   hg graft 149c25c413420120d3f383a9e854a17bc10d96fd
   pip install . --upgrade
   cd ..
   rm -rf py2app
fi

pip install cython
pip install unqlite
pip install mock
pip install pylint
pip install coveralls
pip install wheel
pip install dmgbuild==1.1.0

# pyopenssl is needed because OSX ships an old version of openssl by default
# and python will use it without pyopenssl
pip install PyOpenSSL
pip install jsonrpc
pip install certifi

pip install -r requirements.txt
python packaging/scripts/travis/fix_imp_problems.py
