@echo off

:Flags
set silent=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Office Installer
color 1b
echo Initializing...

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
set "fastcopy=%bin%\FastCopy\FastCopy.exe"
if !arch! equ 64 (
    set "fastcopy=%bin%\FastCopy\FastCopy64.exe"
)
set "fastcopy_args=/cmd=diff /no_ui /auto_close"
rem Create %client_dir%\Office
call "%bin%\Scripts\init_client_dir.cmd" /Office
set "product=%~1"
set "source=\\10.0.0.10\Office\%product%"
set "dest=%client_dir%\Office"

:FileOrFolder
if /i "%source%" == ""          goto UsageError
if /i "%source:~-3,3%" == "exe" goto CopyFile
if /i "%source:~-3,3%" == "msi" goto CopyFile
goto CopyFolder

:CopyFile
if not exist "%source%" goto OfficeNotFound
echo Copying installer...
start "" /wait "%fastcopy%" %fastcopy_args% "%source%" /to="%dest%\%product:0,4%\"
:: Run Setup ::
start "" "%dest%\%product:0,4%\%product:~5%"
goto Done

:CopyFolder
if not exist "%source%\setup.exe" goto OfficeNotFound
echo Copying setup files...
start "" /wait "%fastcopy%" %fastcopy_args% "%source%" /to="%dest%\%product:0,4%\"
:: Run Setup ::
if exist "%dest%\%product:0,4%\configuration.xml" (
    pushd "%dest%\%product:0,4%"
    start "" "setup.exe" /configure
    popd
) else (
    start "" "%dest%\%product:0,4%\setup.exe"
)
goto Done

:: Errors ::
:ErrorNoBin
popd
echo ERROR: ".bin" folder not found.
goto Abort

:OfficeNotFound
echo ERROR: "%source%" not found.
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
echo.
echo Press any key to exit...
pause>nul
goto Exit

:Done
echo.
echo Done.
goto Exit

:Exit
color
endlocal
