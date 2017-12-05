#!/bin/bash
# Wizard Kit: Generic app launcher

# Init
## Get .bin absolute path (dirty code roughly based on http://stackoverflow.com/a/12197227)
pushd . > /dev/null
cd "$(dirname "$0")/../.bin"
BIN="$(pwd)"
popd > /dev/null

# Run
"$BIN/Disk Inventory X.app/Contents/MacOS/Disk Inventory X" &
exit 0
