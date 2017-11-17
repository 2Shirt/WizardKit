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

:RestoreDefaults
del "xmplay.library"
del "xmplay.library~"
del "xmplay.pls"
call "%bin%\Scripts\Launch.cmd" Program "%bin%\XMPlay" "%bin%\7-Zip\7za.exe" "e defaults.7z -aoa -bsp0 -bso0"
ping -n 2 127.0.0.1>nul

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\XMPlay" "xmplay.exe" "music.7z"
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
