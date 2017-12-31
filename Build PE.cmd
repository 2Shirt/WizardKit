:: Wizard Kit: Windows PE Build Tool Launcher ::

@echo off

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Windows PE Build Tool
call :CheckFlags %*
call :CheckElevation || goto Exit
call :FindKitsRoot || goto ErrorKitNotFound

:LaunchPrep
rem Update environment using WADK script
set "dandi_set_env=%adk_root%\Deployment Tools\DandISetEnv.bat"
if not exist "%dandi_set_env%" (goto ErrorKitNotFound)
call "%dandi_set_env%" || goto ErrorUnknown

:EnsureCRLF
rem Rewrite main.py using PowerShell to have CRLF/`r`n lineendings
set "script=%~dp0\.bin\Scripts\borrowed\set-eol.ps1"
set "main=%~dp0\.bin\Scripts\settings\main.py"
powershell -executionpolicy bypass -noprofile -file %script% -lineEnding win -file %main% || goto ErrorUnknown

:Launch
set "script=%~dp0\.bin\Scripts\build_pe.ps1"
powershell -executionpolicy bypass -noprofile -file %script% || goto ErrorUnknown
goto Exit

:: Functions ::
:CheckElevation
rem Code based on StackOverflow comments
rem Question:     https://stackoverflow.com/q/4051883
rem Using answer: https://stackoverflow.com/a/21295806
rem Asked by:     https://stackoverflow.com/users/272237/flacs
rem Edited by:    https://stackoverflow.com/users/330315/a-horse-with-no-name
rem Answer by:    https://stackoverflow.com/users/3198799/and31415
fsutil dirty query %systemdrive% >nul
if %errorlevel% neq 0 (
   call :RequestElevation
   rem reset errorlevel to 1 to abort the current non-elevated script
   color 00
)
@exit /b %errorlevel%

:CheckFlags
rem Loops through all arguments to check for accepted flags
set DEBUG=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on & set "DEBUG=/DEBUG")
)
@exit /b 0

:FindKitsRoot
set "adk_root="
set "found="
set "r_vname=KitsRoot10"

rem Check registry for WADK
set "r_path=HKLM\Software\Wow6432Node\Microsoft\Windows Kits\Installed Roots"
reg query "%r_path%" /v %r_vname% >nul 2>&1 && set "found=True"
if not defined found (
    rem 32-bit systems?
    set "r_path=HKLM\Software\Microsoft\Windows Kits\Installed Roots"
    reg query "!r_path!" /v %r_vname% >nul 2>&1 && set "found=True"
)
for /f "skip=2 tokens=2*" %%i in ('reg query "%r_path%" /v %r_vname%') do (
    set adk_root=%%j\Assessment and Deployment Kit
)
rem Set errorlevel if necessary
if not defined adk_root color 00
if not defined found color 00
@exit /b %errorlevel%

:RequestElevation
set "cscript=%systemroot%\system32\cscript.exe"
set "vb_script=.bin\tmp\Elevate.vbs"
mkdir ".bin\tmp" 2>nul

rem Create VB script
echo Set UAC = CreateObject^("Shell.Application"^) > "%vb_script%"
echo UAC.ShellExecute "%~s0", "", "", "runas", 3 >> "%vb_script%"

rem Run
"%cscript%" //nologo "%vb_script%" || goto ErrorUnknown
del "%vb_script%"
@exit /b 0

:: Errors ::
:ErrorKitNotFound
echo.
echo ERROR: Windows ADK installation not found.
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
