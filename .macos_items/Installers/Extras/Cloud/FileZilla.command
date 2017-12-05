#!/bin/bash

# Init
BIN=""
clear

# Find BIN path
pushd . > /dev/null
cd "$(dirname "$0")"
while [ "$(pwd)" != "/" ]; do
    if [ -d ".bin" ]; then
        BIN="$(pwd)/.bin"
        break
    fi
    cd ..
done
popd > /dev/null
if [ "$BIN" == "" ]; then
    echo ".bin not found"
    exit 1
fi

# Install App(s)
"$BIN/Scripts/install_app" "tar" "FileZilla" "FileZilla.app" "http://downloads.sourceforge.net/project/filezilla/FileZilla_Client/3.21.0/FileZilla_3.21.0_macosx-x86.app.tar.bz2" "" "" ""

# Done
echo ""
