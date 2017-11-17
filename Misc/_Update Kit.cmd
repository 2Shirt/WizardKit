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

:Launch
:: Because this script does not have delayed expansion enabled the '!python!'
:: below is passed verbatim to the Launch.cmd script. This results in
:: Launch.cmd resolving the variable instead. By overriding Launch.cmd in this
:: way we gain two things. First, we take advantage of Launch.cmd's ability to
:: use x64 python if possible. Second, by using the native terminal emulator we
:: avoid the issue in ConEmu where rewriting the same line causes major
:: slowdowns; it can be 5 to 30 times slower than normal.
call "%bin%\Scripts\Launch.cmd" Program "%bin%\Scripts" "!python!" "update_kit.py" /max
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
