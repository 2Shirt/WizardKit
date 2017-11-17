@echo off

:Init
setlocal EnableDelayedExpansion
color 1b
title WK Launcher

:Flags
set admin=
set max=
set wait=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
    if /i "%%f" == "/admin" (@set admin=true)
    if /i "%%f" == "/max" (@set max=true)
    if /i "%%f" == "/wait" (@set wait=true)
)

:SetVariables
if /i "!PROCESSOR_ARCHITECTURE!" == "AMD64" set "arch=64"
set "con=%~dp0\..\..\ConEmu\ConEmu.exe"
if !arch! equ 64 set "con=%~dp0\..\..\ConEmu\ConEmu64.exe"

:Launch
pushd %2
if /i "%1" == "Console"  (goto LaunchConsole)
if /i "%1" == "Office"  (goto LaunchOfficeSetup)
if /i "%1" == "Program"  (goto LaunchProgram)
if /i "%1" == "PSScript" (goto LaunchPSScript)
goto Usage

:LaunchConsole
set "prog=%~3"
dir "!prog:.=64.!" >nul 2>&1 && if !arch! equ 64 set "prog=!prog:.=64.!"
if not exist "!prog!" goto ProgramNotFound
if defined admin (
    start "" "%con%" -cmd "!prog!" %~4 -new_console:a -new_console:n
) else (
    start "" "%con%" -cmd "!prog!" %~4 -new_console:n
)
goto Done

:LaunchOfficeSetup
set "prog=%~3"
start "" "%con%" -cmd call "copy_office.cmd" "!prog!" -new_console:n
goto Done

:LaunchProgram
set "prog=%~3"
dir "!prog:.=64.!" >nul 2>&1 && if !arch! equ 64 set "prog=!prog:.=64.!"
if not exist "!prog!" goto ProgramNotFound
if not "%~4" == "" (set "ps_args=-argumentlist '%~4'")
if defined admin (
    if defined max (set "max=-WindowStyle Maximized")
    if defined wait (set "wait=-Wait")
    powershell -command "& {start '!prog!' !ps_args! -verb runas !max! !wait!}"
) else (
    if defined max (set "max=/max")
    if defined wait (set "wait=/wait")
    start "" !max! !wait! "!prog!" %~4
)
goto Done

:LaunchPSScript
set "script=%~3"
if not exist "!script!" goto ScriptNotFound
if defined wait (set "wait=-Wait")
if defined admin (
    start "" "%con%" -cmd PowerShell -ExecutionPolicy Bypass -File "!script!" -NoProfile -new_console:a !wait!
) else (
    start "" "%con%" -cmd PowerShell -ExecutionPolicy Bypass -File "!script!" -NoProfile !wait!
)
goto Done

:Usage
echo.
echo.Usage: Launch.cmd Console  "Working Dir" "Program" "Args" [/admin]
echo.       Launch.cmd Program  "Working Dir" "Program" "Args" [/admin] [/max] [/wait]
echo.       Launch.cmd PSScript "Working Dir" "Program" ""     [/admin] [/wait]
echo.       (Args should be empty when using PSScript)
echo.
goto Abort

:ProgramNotFound
echo.
echo Program not found.
goto Abort

:ScriptNotFound
echo.
echo Script not found.
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
goto Exit

:Exit
popd
color
endlocal