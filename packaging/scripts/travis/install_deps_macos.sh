#!/bin/sh

set -euo pipefail
set -o xtrace

#if [ ${ON_TRAVIS} = true ]; then
#    wget https://www.python.org/ftp/python/2.7.11/python-2.7.11-macosx10.6.pkg
#    sudo installer -pkg python-2.7.11-macosx10.6.pkg -target /
#    pip install -U pip
#fi

pip install -U pip --upgrade

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


if brew ls --versions hg > /dev/null; then
    echo 'hg is already installed by brew'
else
    brew install hg
fi

if brew ls --versions wget > /dev/null; then
    echo 'wget is already installed by brew'
else
    brew install wget
fi

#MODULES="pyobjc-core==3.1.1 pyobjc-framework-Cocoa==3.1.1 pyobjc-framework-CFNetwork==3.1.1 pyobjc-framework-Quartz==3.1.1"

if [ ${ON_TRAVIS} = true ]; then
    mkdir wheels
    cd wheels
    wget https://s3.amazonaws.com/files.lbry.io/wheels.zip
    unzip wheels.zip
    rm wheels.zip
    pip install ./*.whl --no-deps
    cd ..
fi

pip install modulegraph==0.13
pip install hg+https://bitbucket.org/jackrobison/py2app
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
