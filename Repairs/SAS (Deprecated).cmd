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
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "SAS.exe" "" /wait

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%programfiles%\SUPERAntiSpyware" "SUPERAntiSpyware.exe" ""
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
