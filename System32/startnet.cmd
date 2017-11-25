@echo off

echo Initializing...
wpeinit
wpeutil updatebootinfo

pushd %systemdrive%\WK
set "PATH=%PATH%;%systemdrive%\WK"

powershell -executionpolicy bypass -file %systemdrive%\WK\Scripts\WK.ps1
