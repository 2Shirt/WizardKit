@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 creation tool
color 1b
pushd %~dp0
set "wd=%cd%"
set "pe_iso=WinPE-2016-02d.iso"

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CreateISO
del "!pe_iso!"
makewinpemedia.cmd /iso "%wd%\pe_files" "!pe_iso!"
goto Done

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