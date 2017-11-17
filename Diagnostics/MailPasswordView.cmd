@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:FindBin
set bin=
pushd "%~dp0"
:FindBinInner
if exist ".bin" (
    set "bin=%cd%\.bin"
    goto FindBinDone
)
if "%~d0\" == "%cd%" (
    goto FindBinDone
) else (
    cd ..
)
goto FindBinInner
:FindBinDone
popd
if not defined bin goto ErrorNoBin

:Init
setlocal enabledelayedexpansion

:Extract
mkdir "%bin%\tmp" >nul 2>&1
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "%bin%\7-Zip\7za.exe" "x mailpv.7z -otmp -aoa -pAbracadabra -bsp0 -bso0" /wait
ping -n 1 127.0.0.1>nul

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\tmp" "mailpv.exe" ""

:Done
popd
endlocal
goto Exit

:ErrorNoBin
color 4e
echo ".bin" folder not found, aborting script.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:Exit
