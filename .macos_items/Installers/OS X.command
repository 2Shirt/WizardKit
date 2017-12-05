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
"$BIN/Scripts/install_app" "dmg" "Firefox" "Firefox.app" "http://download.mozilla.org/?product=firefox-latest&os=osx&lang=en-US" "" "" ""
"$BIN/Scripts/install_app" "dmg" "Chrome" "Google Chrome.app" "https://dl.google.com/chrome/mac/stable/GGRO/googlechrome.dmg" "" "" ""
"$BIN/Scripts/install_app" "dmg" "MBAM" "Malwarebytes Anti-Malware.app" "https://store.malwarebytes.org/342/purl-mbamm-dl" "" "" ""
"$BIN/Scripts/install_app" "zip" "iTerm2" "iTerm.app" "https://iterm2.com/downloads/stable/iTerm2-3_0_9.zip" "" "" ""
"$BIN/Scripts/install_app" "zip" "macsfancontrol" "Macs Fan Control.app" "http://www.crystalidea.com/downloads/macsfancontrol.zip" "" "" ""
"$BIN/Scripts/install_app" "dmg" "Spotify" "Spotify.app" "http://download.spotify.com/Spotify.dmg" "" "" ""
"$BIN/Scripts/install_app" "dmg" "VLC" "VLC.app" "http://get.videolan.org/vlc/2.2.4/macosx/vlc-2.2.4.dmg" "" "" ""
"$BIN/Scripts/install_app" "tgz" "mpv" "mpv.app" "https://laboratory.stolendata.net/~djinn/mpv_osx/mpv-latest.tar.gz" "" "" ""

# Done
echo ""
