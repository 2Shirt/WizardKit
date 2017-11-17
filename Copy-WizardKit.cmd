@echo off

:Flags
set silent=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
title Wizard Kit Copier
color 1b
echo Initializing...

:FindWizardKit
set wrongpath=
call :TestSource "%~dp0"
if defined wrongpath (call :TestSource "\\10.0.0.10\WizardKit")
if defined wrongpath goto WizardKitNotFound

:Vars
rem :TestSource above runs pushd, so %cd% should be accurate.
set "source=%cd%"
set "dest=%systemdrive%\WK\Tools"

:CreateToolsFolder
mkdir "!dest!" > nul 2>&1

:: .bin folder ::
set "args="
call :RoboCopy "!source!\.bin" "!dest!\.bin" "" "!args!"

:: RKill Alternatives ::
pushd "!dest!\.bin\RKill"
mklink /h explorer.exe RKill.exe
mklink /h iExplore.exe RKill.exe
mklink /h RKill.com RKill.exe
mklink /h RKill.scr RKill.exe
mklink /h uSeRiNiT.exe RKill.exe
mklink /h WiNlOgOn.exe RKill.exe
popd

:: Root files ::
set "args="
call :RoboCopy "!source!\.bin\Scripts" "!dest!\.bin\Scripts" "" "!args!"
copy /y "!source!\Battery Health.cmd" "!dest!\"
copy /y "!source!\Enter SafeMode.cmd" "!dest!\"
copy /y "!source!\Exit SafeMode.cmd" "!dest!\"
copy /y "!source!\Final Checklist.cmd" "!dest!\"
copy /y "!source!\Reset Browsers.cmd" "!dest!\"
copy /y "!source!\SW Diagnostics.cmd" "!dest!\"

:: Activation ::
set "args="
call :RoboCopy "!source!\Activation" "!dest!\Activation" "" "!args!"

:: Data Recovery ::
rem Disabled.
rem set "args="
rem call :RoboCopy "!source!\Data Recovery" "!dest!\Data Recovery" "" "!args!"

:: Data Transfers & DSR ::
set "args="
call :RoboCopy "!source!\Data Transfers & DSR" "!dest!\Data Transfers & DSR" "" "!args!"

:: Diagnostics ::
set "args="
call :RoboCopy "!source!\Diagnostics" "!dest!\Diagnostics" "" "!args!"

:: Drivers ::
set "args="
call :RoboCopy "!source!\Drivers" "!dest!\Drivers" "" "!args!"

:: Installers ::
set "args="
call :RoboCopy "!source!\Installers" "!dest!\Installers" "" "!args!"

:: Misc ::
set "args="
call :RoboCopy "!source!\Misc" "!dest!\Misc" "" "!args!"

:: OSR & VR ::
set "args="
call :RoboCopy "!source!\OSR & VR" "!dest!\OSR & VR" "" "!args!"

:: Uninstallers ::
set "args="
call :RoboCopy "!source!\Uninstallers" "!dest!\Uninstallers" "" "!args!"

:: Open Folder ::
start "" explorer "!dest!"
goto Done

:: Subroutines ::
:RoboCopy
rem set args (without quotes)
set "_source=%~1"
set "_dest=%~2"
set "_files=%~3"
set "_args=%~4"
mkdir "!_dest!" >nul 2>&1
robocopy /s /r:3 /w:0 "!_source!" "!_dest!" !_files! !_args!
goto :EOF

:TestSource
set wrongpath=
:: Testing one for one dir is probably enough.
dir "Uninstallers" >nul 2>&1
if %errorlevel% neq 0 (set wrongpath=true)
if not defined wrongpath (pushd "%1")
goto :EOF

:WizardKitNotFound
echo ERROR: WizardKit not found.
goto Abort

:WindowsVersionError
echo ERROR: This version of Windows is not supported.
goto Abort

:Abort
color 4e
echo.
echo Aborted.
echo.
echo Press any key to exit...
pause>nul
goto Exit

:Done
echo.
echo Done.
goto Exit

:Exit
popd
color
endlocal

:EOF
