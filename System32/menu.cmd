@echo off

:Init
setlocal EnableDelayedExpansion
title Menu Launcher
color 0a
pushd %~dp0

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:LaunchMenu
PowerShell -ExecutionPolicy Bypass %systemdrive%\WK\Scripts\WK.ps1
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
rem echo Press any key to exit...
rem pause>nul
popd
color
endlocal