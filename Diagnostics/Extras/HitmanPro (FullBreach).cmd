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

:CreateInfoDir
rem Create %client_dir%\Info\YYYY-MM-DD and set path as %log_dir%
call "%bin%\Scripts\init_client_dir.cmd" /Info

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\HitmanPro" "HitmanPro.exe" "/scan /noinstall /noupload /log=%log_dir%\hitman.xml /fb" /admin
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
