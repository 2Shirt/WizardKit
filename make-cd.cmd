@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 creation tool
color 1b
pushd %~dp0

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CreateISO
del winpe10-test.iso
makewinpemedia.cmd /iso wd winpe10-test.iso

:Abort
echo.
echo Aborted.
goto Exit

:Done
echo.
echo Done.
goto Exit

:Exit
echo.
echo Press any key to exit...
pause>nul
popd
color
endlocal