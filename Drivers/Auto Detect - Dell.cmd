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
echo Waiting for software installation to finish...
call "%bin%\Scripts\Launch.cmd" Program "%bin%\_Drivers" "Dell System Detect.exe" "" /admin /wait
start "" "http://www.dell.com/support/home/us/en/19/Eula/scan?sourcePage=J&scanType=TMC&loadSection=N&AppName=drivers&app=drivers"
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
