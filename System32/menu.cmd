@echo off

:Init
setlocal EnableDelayedExpansion
title Menu Launcher
color 0b
pushd %~dp0

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:LaunchMenu
"%SystemDrive%\WK\ConEmu\ConEmu.exe" /cmd PowerShell -ExecutionPolicy Bypass "%SystemDrive%\WK\Scripts\WK.ps1" -NoProfile -new_console:n
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
popd
endlocal
