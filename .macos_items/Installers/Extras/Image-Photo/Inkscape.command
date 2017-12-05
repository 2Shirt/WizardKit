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
"$BIN/Scripts/install_app" "dmg" "Inkscape" "Inkscape.app" "https://inkscape.org/en/gallery/item/3896/Inkscape-0.91-1-x11-10.7-x86_64.dmg" "" "" ""

# Done
echo ""
