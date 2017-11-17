@echo off

:Flags
set silent=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
title WK Office Installer
color 1b
echo Initializing...
set "pd=%cd%"
set "NAS=\\10.0.0.10\Office"
set "dest=%systemdrive%\WK\Office"
set "source=%~1"
pushd !NAS!

:VerifyCopyAndRun
if /i "!source!" == "" (goto UsageError)

if /i "!source:~-3,3!" == "exe" (
    if not exist "!source!" goto OfficeNotFound
    call :CopyFile "!source!"
) else if /i "!source:~-3,3!" == "msi" (
    if not exist "!source!" goto OfficeNotFound
    call :CopyFile "!source!"
) else (
    if not exist "!source!\setup.exe" goto OfficeNotFound
    call :CopyFolder "!source!"
)
goto Done

:: Sub-routines ::
:CopyFile
set "file=%~1"
echo Copying files...
mkdir "!dest!" > nul 2>&1
robocopy /r:3 /w:0 "!file:~0,4!" "!dest!" "!file:~5!"
:: Run Setup ::
start "" "!dest!\!file:~5!"
goto :EOF

:CopyFolder
set "folder=%~1"
mkdir "!dest!\!folder!" > nul 2>&1
robocopy /s /r:3 /w:0 "!folder!" "!dest!\!folder!"
:: Run Setup ::
if exist "!dest!\!folder!\configuration.xml" (
    pushd "!dest!\!folder!"
    start "" "setup.exe" /configure
    popd
) else (
    start "" "!dest!\!folder!\setup.exe"
)
goto :EOF

:: Errors ::
:OfficeNotFound
echo ERROR: "!source!" not found.
goto Abort

:UsageError
echo ERROR: Office version not specified.
echo.
echo USAGE: "%~nx0" "Path\To\Office\Setup"
goto Abort

:Abort
color 4e
echo.
echo Aborted.
goto Exit

:Done
set silent=true
echo.
echo Done.
goto Exit

:Exit
rem if not defined silent (
rem     echo Press any key to exit...
rem     pause>nul
rem )
popd
color
endlocal

:EOF
