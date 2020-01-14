:: Wizard Kit: Build Tool Launcher ::

@echo off

:Init
setlocal
title Wizard Kit: Build Tool
call :CheckFlags %*

:PrepNewKit
rem Copy base files to a new folder OUT_KIT
robocopy /e .kit_items OUT_KIT
robocopy /e .bin OUT_KIT\.bin
robocopy /e .cbin OUT_KIT\.cbin
copy LICENSE.txt OUT_KIT\LICENSE.txt
copy README.md OUT_KIT\README.md
copy Images\ConEmu.png OUT_KIT\.bin\ConEmu\
mkdir OUT_KIT\.cbin >nul 2>&1
attrib +h OUT_KIT\.bin >nul 2>&1
attrib +h OUT_KIT\.cbin >nul 2>&1

:EnsureCRLF
rem Rewrite main.py using PowerShell to have CRLF/`r`n lineendings
set "script=OUT_KIT\.bin\Scripts\borrowed\set-eol.ps1"
set "main=OUT_KIT\.bin\Scripts\settings\main.py"
powershell -executionpolicy bypass -noprofile -file %script% -lineEnding win -file %main% || goto ErrorUnknown

:Launch
set "script=OUT_KIT\.bin\Scripts\build_kit.ps1"
powershell -executionpolicy bypass -noprofile -file %script% || goto ErrorUnknown
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
