@echo off

:Init
setlocal enabledelayedexpansion
pushd %~dp0\..\.bin

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Extract
mkdir "OutlookAttachView" >nul 2>&1
7-Zip\7z.exe x OutlookAttachView.7z -oOutlookAttachView -aos -pAbracadabra -bsp0 -bso0
ping -n 1 127.0.0.1>nul

:Launch
call "Scripts\Launch.cmd" Program "OutlookAttachView" "OutlookAttachView.exe" "" /admin

:Done
popd
endlocal