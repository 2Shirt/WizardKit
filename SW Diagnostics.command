#!/bin/bash
# Wizard Kit: Start SW Diagnostics

# Init
## Get .bin absolute path (dirty code roughly based on http://stackoverflow.com/a/12197227)
pushd . > /dev/null
cd "$(dirname "$0")/.bin"
BIN="$(pwd)"
popd > /dev/null

# Run
sudo "$BIN/Scripts/diagnostics"
exit 0
