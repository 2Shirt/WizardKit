:: Wizard Kit: Wrapper for launching programs and scripts.
::
:: Some features:
::   * If the OS is 64-bit then the WorkingDir is scanned for a 64-bit version of the programs
::   * Allows for centralized terminal emulation settings management
::   * Allows for smaller "launcher" scripts to be used as they will rely on this script.

@echo off

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Launcher

:Flags
set admin=
set max=
set wait=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
    if /i "%%f" == "/admin" (set admin=true)
    if /i "%%f" == "/max" (set max=true)
    if /i "%%f" == "/wait" (set wait=true)
)

:FindBin
set bin= & pushd "%~dp0"
:FindBinInner
if exist ".bin" goto FindBinDone
if "%~d0\" == "%cd%" goto ErrorNoBin
cd .. & goto FindBinInner
:FindBinDone
set "bin=%cd%\.bin" & popd

:SetVariables
if /i "!PROCESSOR_ARCHITECTURE!" == "AMD64" set "arch=64"
set "con=%bin%\ConEmu\ConEmu.exe"
set "python=%bin%\Python\x32\python.exe"
if !arch! equ 64 (
    set "con=%bin%\ConEmu\ConEmu64.exe"
    set "python=%bin%\Python\x64\python.exe"
)

:Launch
pushd "%2"
if /i "%1" == "Console"  (goto LaunchConsole)
if /i "%1" == "Office"  (goto LaunchOfficeSetup)
if /i "%1" == "Program"  (goto LaunchProgram)
if /i "%1" == "PSScript" (goto LaunchPSScript)
if /i "%1" == "PyScript" (goto LaunchPyScript)
goto Usage

:LaunchConsole
set "prog=%~3"
if !arch! equ 64 (
    if exist "!prog:.=64.!" set "prog=!prog:.=64.!"
)
if not exist "!prog!" goto ProgramNotFound
if defined admin (
    start "" "%con%" -cmd "!prog!" %~4 -new_console:a -new_console:n
) else (
    start "" "%con%" -cmd "!prog!" %~4 -new_console:n
)
goto Done

:LaunchOfficeSetup
set "prog=%~3"
start "" "%con%" -cmd call "%bin%\copy_office.cmd" "!prog!" -new_console:n
goto Done

:LaunchProgram
set "prog=%~3"
if !arch! equ 64 (
    if exist "!prog:.=64.!" set "prog=!prog:.=64.!"
)
if not exist "!prog!" goto ProgramNotFound
if not "%~4" == "" (set "vb_args=%~4")
if defined admin (
    mkdir "%bin%\tmp"
    echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
    echo UAC.ShellExecute "!prog!", "!vb_args!", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"
    cscript //nologo "%bin%\tmp\Elevate.vbs"
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
    start "" "%con%" -run PowerShell -ExecutionPolicy Bypass -File "!script!" -NoProfile -new_console:a !wait!
) else (
    start "" "%con%" -run PowerShell -ExecutionPolicy Bypass -File "!script!" -NoProfile !wait!
)
goto Done

:LaunchPyScript
set "script=%~3"
if not exist "!script!" goto ScriptNotFound
if defined admin (
    start "" "%con%" -run "%python%" "!script!" -new_console:a -new_console:n
) else (
    start "" "%con%" -run "%python%" "!script!" -new_console:n
)
goto Done

:Usage
echo.
echo.Usage: Launch.cmd Console  "Working Dir" "Program" "Args" [/admin]
echo.       Launch.cmd Office   "Working Dir" "Product" ""
echo.       Launch.cmd Program  "Working Dir" "Program" "Args" [/admin] [/max] [/wait]
echo.       Launch.cmd PSScript "Working Dir" "Program" ""     [/admin] [/wait]
echo.       Launch.cmd PyScript "Working Dir" "Program" ""     [/admin]
echo.       (Args should be empty when using PSScript or PyScript)
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
endlocal