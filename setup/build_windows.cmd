:: WizardKit: Windows Kit Build Tool ::

@echo off

:Init
setlocal EnableDelayedExpansion
pushd "%~dp0"
title WizardKit: Build Tool
call :CheckFlags %*

:SetVariables
rem Set variables using settings\main.py file
set "SETTINGS=..\scripts\wk\cfg\main.py"
for %%v in (KIT_NAME_FULL) do (
  set "var=%%v"
  for /f "tokens=* usebackq" %%f in (`findstr "!var!=" "%SETTINGS%"`) do (
    set "_v=%%f"
    set "_v=!_v:*'=!"
    set "%%v=!_v:~0,-1!"
  )
)
set "OUT_DIR=OUT_KIT\%KIT_NAME_FULL%"

:PrepNewKit
rem Copy base files to a new folder %OUT_DIR%
mkdir %OUT_DIR% >nul 2>&1
robocopy /e windows/bin %OUT_DIR%\.bin
robocopy /e ..\scripts %OUT_DIR%\.bin\Scripts
rem robocopy /e windows/cbin %OUT_DIR%\.cbin
mkdir %OUT_DIR%\.cbin
copy ..\LICENSE.txt %OUT_DIR%\LICENSE.txt
copy ..\README.md %OUT_DIR%\README.md
copy ..\images\ConEmu.png %OUT_DIR%\.bin\ConEmu\
attrib +h %OUT_DIR%\.bin >nul 2>&1
attrib +h %OUT_DIR%\.cbin >nul 2>&1

:Launch
set "script=windows\build.ps1"
powershell -executionpolicy bypass -noprofile -file %script% "%OUT_DIR%" || goto ErrorUnknown
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
popd
endlocal
exit /b %errorlevel%
