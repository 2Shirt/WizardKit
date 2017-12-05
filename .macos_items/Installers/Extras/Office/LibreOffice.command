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
"$BIN/Scripts/install_app" "dmg" "LibreOffice" "LibreOffice.app" "http://download.documentfoundation.org/libreoffice/stable/5.1.5/mac/x86_64/LibreOffice_5.1.5_MacOS_x86-64.dmg" "" "" ""

# Done
echo ""
