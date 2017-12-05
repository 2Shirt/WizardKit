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
"$BIN/Scripts/install_app" "dmg" "OpenOffice" "OpenOffice.app" "http://downloads.sourceforge.net/project/openofficeorg.mirror/4.1.2/binaries/en-US/Apache_OpenOffice_4.1.2_MacOS_x86-64_install_en-US.dmg" "" "" ""

# Done
echo ""
