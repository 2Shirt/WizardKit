@echo off

:Flags
set silent=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
title WK Tools Copier
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

:OS-Check
set "os_supported="
for /f "tokens=3*" %%v in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentVersion 2^>nul') do (set "win_ver=%%v")
for /f "tokens=3*" %%b in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuildNumber 2^>nul') do (set "win_build=%%b")

if "!win_ver!" == "6.0" (
    set "os_supported=true"
    set "win_version=Vista"
)
if "!win_ver!" == "6.1" (
    set "os_supported=true"
    set "win_version=7"
)
if "!win_ver!" == "6.2" (
    set "os_supported=true"
    set "win_version=8"
)
if "!win_ver!" == "6.3" (
    set "os_supported=true"
    set "win_version=8"
    if "!win_build!" == "10240" (
        set "win_version=10"
    )
    if "!win_build!" == "10586" (
        set "win_version=10"
    )
)

rem !win_ver!.!win_build!
rem == vista ==
rem 6.0.6000
rem 6.0.6001
rem 6.0.6002
rem ==== 7 ====
rem 6.1.7600
rem 6.1.7601
rem 6.1.7602
rem ==== 8 ====
rem 6.2.9200
rem === 8.1 ===
rem 6.3.9200
rem === 8.1u ==
rem 6.3.9600
rem === 10 ==
rem 6.3.10240
rem === 10 v1511 ==
rem 6.3.10586

if not defined os_supported (goto WindowsVersionError)

:CreateToolsFolder
mkdir "!dest!" > nul 2>&1

:: .bin folder ::
set "args=/xd Scripts"
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

:: Scripts ::
set "args=/xf update-tools
call :RoboCopy "!source!\.bin\Scripts" "!dest!\.bin\Scripts" "" "!args!"
if !win_version! equ 8  (copy /y "!source!\Activate Windows 8.cmd" "!dest!\")
if !win_version! equ 10  (copy /y "!source!\Activate Windows 8.cmd" "!dest!\Activate Windows (with BIOS key).cmd")
copy /y "!source!\Battery Health.cmd" "!dest!\"
copy /y "!source!\Enter SafeMode.cmd" "!dest!\"
copy /y "!source!\Exit SafeMode.cmd" "!dest!\"
copy /y "!source!\Hide Windows 10 Upgrade.reg" "!dest!\"
copy /y "!source!\Reset Browsers.cmd" "!dest!\"
move /y "!dest!\.bin\Scripts\Final Checklist.cmd" "!dest!\"
move /y "!dest!\.bin\Scripts\SW Diagnostics.cmd" "!dest!\"

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
if not defined wrongpath (pushd %1)
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
