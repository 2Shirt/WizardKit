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
"$BIN/Scripts/install_app" "zip" "Plex" "Plex Media Server.app" "https://downloads.plex.tv/plex-media-server/0.9.16.6.1993-5089475/PlexMediaServer-0.9.16.6.1993-5089475-OSX.zip" "" "" ""

# Done
echo ""
