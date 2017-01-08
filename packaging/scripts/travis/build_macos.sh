#!/bin/bash

set -o errexit
set -o xtrace

DEST=`pwd`
tmp="${DEST}/build"

rm -rf build dist LBRY.app

if [ ${ON_TRAVIS} = true ]; then
    export PATH=${PATH}:/Library/Frameworks/Python.framework/Versions/2.7/bin
fi

NAME=`python setup.py --name`
VERSION=`python setup.py -V`

if [ -z ${SKIP_PYLINT+x} ]; then
    ./packaging/scripts/travis/run_pylint.sh packaging/tray_app/macos/
fi

echo "Building URI Handler"

rm -rf build dist
python packaging/uri_handler/build_macos.py py2app

if [ ${SKIP_SIGN} = false ]; then
    echo "Signing URI Handler"
    codesign -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRYURIHandler.app/Contents/Frameworks/Python.framework/Versions/2.7"
    codesign -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRYURIHandler.app/Contents/MacOS/python"
    # not sure if --deep is appropriate here, but need to get LBRYURIHandler.app/Contents/Frameworks/libcrypto.1.0.0.dylib signed
    codesign --deep -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRYURIHandler.app/Contents/MacOS/LBRYURIHandler"
    codesign -vvvv "${DEST}/dist/LBRYURIHandler.app"
fi

# py2app will skip _cffi_backend without explicitly including it
# and without this, we will get SSL handshake errors when connecting
# to bittrex
python packaging/tray_app/build_macos.py py2app -i _cffi_backend

echo "Removing i386 libraries"

remove_arch () {
    if [[ `lipo "$2" -verify_arch "$1"` ]]; then
       lipo -output build/lipo.tmp -remove "$1" "$2" && mv build/lipo.tmp "$2"
    fi
}

for i in `find dist/LBRY.app/Contents/Resources/lib/python2.7/lib-dynload/ -name "*.so"`; do
    remove_arch i386 $i
done


echo "Moving LBRYURIHandler.app into LBRY.app"
mv "${DEST}/dist/LBRYURIHandler.app" "${DEST}/dist/LBRY.app/Contents/Resources"

if [ ${SKIP_SIGN} = false ]; then
    echo "Signing LBRY.app"
    codesign -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRY.app/Contents/Frameworks/Python.framework/Versions/2.7"
    codesign -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRY.app/Contents/Frameworks/libgmp.10.dylib"
    codesign -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRY.app/Contents/MacOS/python"
    # adding deep here as well because of subcomponent issues
    codesign --deep -s "${LBRY_DEVELOPER_ID}" -f "${DEST}/dist/LBRY.app/Contents/MacOS/LBRY"
    codesign -vvvv "${DEST}/dist/LBRY.app"
fi

rm -rf $tmp
mv dist/LBRY.app LBRY.app

if [ ${SKIP_DMG} = false ]; then
    rm -rf dist "${NAME}.${VERSION}.dmg"
    dmgbuild -s ./packaging/scripts/travis/dmg_settings.py "LBRY" "${NAME}.${VERSION}.dmg"
fi
