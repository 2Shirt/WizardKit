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

:Configure
rem just configure for both x32 & x64
for %%a in (32 64) do (
    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"
    (echo SensorsOnly=1)>>"%bin%\HWiNFO\HWiNFO%%a.ini"
    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"
)

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\HWiNFO" "HWiNFO.exe" ""
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
