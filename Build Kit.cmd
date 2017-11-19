:: Wizard Kit: Build Tool Launcher ::

@echo off

:Init
setlocal
call :CheckFlags %*
title Wizard Kit: Build Tool

:LaunchPrep
rem Verifies the environment before launching item
if not exist ".bin\Scripts\build_kit.ps1" (goto ErrorBuildKitMissing)

:Launch
rem Calls the Launch.cmd script using the variables defined above
powershell -executionpolicy bypass -noprofile -file .bin\Scripts\build_kit.ps1 || goto ErrorUnknown
goto Exit

:: Functions ::
:CheckFlags
rem Loops through all arguments to check for accepted flags
set DEBUG=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on & set "DEBUG=/DEBUG")
)
@exit /b 0

:: Errors ::
:ErrorBuildKitMissing
echo.
echo ERROR: build_kit.ps1 script not found.
goto Abort

:ErrorUnknown
echo.
echo ERROR: Encountered an unknown error.
goto Abort

:Abort
color 4e
echo Aborted.
echo.
echo Press any key to exit...
pause>nul
color
rem Set errorlevel to 1 by calling color incorrectly
color 00
goto Exit

:: Cleanup and exit ::
:Exit
endlocal
exit /b %errorlevel%
