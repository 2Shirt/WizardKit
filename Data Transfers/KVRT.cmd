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

:CreateQuarantineDir
set "q_dir=%systemdrive%\WK\Quarantine\KVRT"
mkdir "%q_dir%">nul 2>&1

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "KVRT.exe" "-accepteula -d %q_dir% -processlevel 3 -dontcryptsupportinfo -fixednames"
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
