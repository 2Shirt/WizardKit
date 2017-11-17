@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:FindBin
set bin= & pushd "%~dp0"
:FindBinInner
if exist ".bin" goto FindBinDone
if "%~d0\" == "%cd%" goto ErrorNoBin
cd .. & goto FindBinInner
:FindBinDone
set "bin=%cd%\.bin" & popd

:Init
setlocal EnableDelayedExpansion

:ClearConfigs
if not exist "%bin%\tmp" goto Extract
pushd "%bin%\tmp"
if exist "ProduKey.cfg" del "ProduKey.cfg"
if exist "ProduKey64.cfg" del "ProduKey64.cfg"
popd

:Extract
cls
mkdir "%bin%\tmp" >nul 2>&1
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "%bin%\7-Zip\7za.exe" "e ProduKey.7z -otmp -aoa -pAbracadabra -bsp0 -bso0" /wait
ping -n 2 127.0.0.1>nul

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\tmp" "ProduKey.exe" "" /admin

:Done
endlocal
goto Exit

:ErrorNoBin
popd
color 4e
echo ".bin" folder not found, aborting script.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:Exit
