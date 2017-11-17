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

:RestoreDefaults
del "xmplay.library"
del "xmplay.library~"
del "xmplay.pls"
call "%bin%\Scripts\Launch.cmd" Program "%bin%\XMPlay" "%bin%\7-Zip\7za.exe" "e defaults.7z -aoa -bsp0 -bso0"

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\XMPlay" "xmplay.exe" "music.7z"
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
