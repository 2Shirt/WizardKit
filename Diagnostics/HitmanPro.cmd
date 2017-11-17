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

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as %log_dir%
call "%bin%\Scripts\wk_info.cmd"

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\HitmanPro" "HitmanPro.exe" "/scan /noinstall /noupload /log=%log_dir%\hitman.xml" /admin
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
