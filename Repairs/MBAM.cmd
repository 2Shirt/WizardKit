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

:Install
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "MBAM.exe" "" /wait

:Launch
if exist "%programfiles%\Malwarebytes Anti-Malware\mbam.exe" (call "%bin%\Scripts\Launch.cmd" Program "%programfiles%\Malwarebytes Anti-Malware" "mbam.exe" "")
if exist "%programfiles(x86)%\Malwarebytes Anti-Malware\mbam.exe" (call "%bin%\Scripts\Launch.cmd" Program "%programfiles(x86)%\Malwarebytes Anti-Malware" "mbam.exe" "")
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
