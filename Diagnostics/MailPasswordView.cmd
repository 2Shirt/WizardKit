@echo off

:Init
setlocal enabledelayedexpansion
pushd %~dp0\..\.bin

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Extract
mkdir "mailpv" >nul 2>&1
7-Zip\7z.exe x mailpv.7z -omailpv -aos -pAbracadabra -bsp0 -bso0
ping -n 1 127.0.0.1>nul

:Launch
call "Scripts\Launch.cmd" Program "mailpv" "mailpv.exe" ""

:Done
popd
endlocal