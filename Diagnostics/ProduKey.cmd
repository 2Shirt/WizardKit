@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
pushd %~dp0\..\.bin

:ClearConfigs
if exist "ProduKey\*.*" (
    pushd ProduKey
    if exist "ProduKey.cfg" del "ProduKey.cfg"
    if exist "ProduKey64.cfg" del "ProduKey64.cfg"
    popd
)

:FindHives
set choices=L
echo.L: ~Local System~
set "_S=%systemdrive%\WK\Transfer\Software"
if exist "!_S!" (
    set "choices=!choices!S"
    echo.S: !_S!
)
set "_T=%systemdrive%\WK\Transfer\Windows\System32\config\Software"
if exist "!_T!" (
    set "choices=!choices!T"
    echo.T: !_T!
)
set "_O=%systemdrive%\WK\Transfer\Windows.old\Windows\System32\config\Software"
if exist "!_O!" (
    set "choices=!choices!O"
    echo.O: !_O!
)
set "_P=%systemdrive%\WK\Transfer\Windows.old\Software"
if exist "!_P!" (
    set "choices=!choices!P"
    echo.P: !_P!
)

:Choose
echo.
set "args="

rem If there are no choices, then don't ask
if "!choices!" == "L" (goto Extract)

rem pick souce and use response to set sw_hive
choice /c !choices! /t 10 /d l /m "Please select source"
set /a "index=!errorlevel! - 1"
set "choice=!choices:~%index%,1!"

rem Transferred hives
if "!choice!" == "S" (set "sw_hive=!_S!")
if "!choice!" == "T" (set "sw_hive=!_T!")
if "!choice!" == "O" (set "sw_hive=!_O!")
if "!choice!" == "P" (set "sw_hive=!_P!")

rem set args
if !index! neq 0 (set "args=/regfile !sw_hive!")

:Extract
cls
mkdir "ProduKey" >nul 2>&1
7-Zip\7z.exe x ProduKey.7z -oProduKey -aos -pAbracadabra -bsp0 -bso0
ping -n 1 127.0.0.1>nul

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\ProduKey" "ProduKey.exe" "!args!" /admin

:Done
popd
endlocal