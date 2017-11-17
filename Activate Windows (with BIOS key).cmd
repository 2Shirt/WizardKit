@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Extract
pushd %~dp0\..\.bin
cls
mkdir "ProduKey" >nul 2>&1
7-Zip\7z.exe x ProduKey.7z -oProduKey -aos -pAbracadabra -bsp0 -bso0
ping -n 1 127.0.0.1>nul
popd

:Launch
call "%~dp0\.bin\Scripts\Launch.cmd" PSScript "%~dp0\.bin\Scripts" "activate.ps1" /admin