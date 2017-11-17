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

:Install
call "%bin%\Scripts\Launch.cmd" Program "%bin%\..\Installers\Extras\Security" "Malwarebytes Anti-Malware.exe" "" /wait

:Launch
if exist "%programfiles%\Malwarebytes Anti-Malware\mbam.exe" (call "%bin%\Scripts\Launch.cmd" Program "%programfiles%\Malwarebytes Anti-Malware" "mbam.exe" "")
if exist "%programfiles(x86)%\Malwarebytes Anti-Malware\mbam.exe" (call "%bin%\Scripts\Launch.cmd" Program "%programfiles(x86)%\Malwarebytes Anti-Malware" "mbam.exe" "")
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
