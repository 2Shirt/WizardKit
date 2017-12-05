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
"$BIN/Scripts/install_app" "dmg" "Google Chrome" "Google Chrome.app" "https://dl.google.com/chrome/mac/stable/GGRO/googlechrome.dmg" "" "" ""

# Done
echo ""
