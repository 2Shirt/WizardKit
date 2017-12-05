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
"$BIN/Scripts/install_app" "dmg" "HandBrake" "HandBrake.app" "http://downloads.sourceforge.net/project/handbrake/0.10.5/HandBrake-0.10.5-MacOSX.6_GUI_x86_64.dmg" "" "" ""

# Done
echo ""
