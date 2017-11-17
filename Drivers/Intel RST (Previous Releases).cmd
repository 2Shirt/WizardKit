:: Wizard Kit: Launcher Script ::
::
:: This script works by setting env variables and then calling Launch.cmd
:: which inherits the variables. This bypasses batch file argument parsing
:: which is awful.
@echo off

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Launcher
call :CheckFlags %*
call :FindBin
call :SetTitle Launcher

:DefineLaunch
:: Set L_TYPE to one of these options:
::     Console, Folder, Office, Program, PSScript, or PyScript
:: Set L_PATH to the path to the program folder
:: NOTE: Launch.cmd will test for L_PATH in the following order:
::      1: %cbin%\L_PATH.7z (which will be extracted to %bin%\L_PATH)
::      2: %bin%\L_PATH
::      3. %L_PATH%         (i.e. treat L_PATH as an absolute path)
:: Set L_ITEM to one of the following:
::      1. The filename of the item to launch
::      2. The Office product to install
::      3. '.' to open extracted folder
:: Set L_ARGS to include any necessary arguments (if any)
:: Set L_7ZIP to include any necessary arguments for extraction
:: Set L_CHCK to True to have Launch.cmd to stay open if an error is encountered
:: Set L_ELEV to True to launch with elevated permissions
:: Set L_NCMD to True to stay in the native console window
:: Set L_WAIT to True to have the script wait until L_ITEM has comlpeted
set L_TYPE=Folder
set L_PATH=_Drivers\Intel RST
set L_ITEM=.
set L_ARGS=
set L_7ZIP=
set L_CHCK=True
set L_ELEV=
set L_NCMD=True
set L_WAIT=

:::::::::::::::::::::::::::::::::::::::::::
:: Do not edit anything below this line! ::
:::::::::::::::::::::::::::::::::::::::::::

:LaunchPrep
rem Verifies the environment before launching item
if not defined bin (goto ErrorNoBin)
if not exist "%bin%\Scripts\Launch.cmd" (goto ErrorLaunchCMDMissing)

:Launch
rem Calls the Launch.cmd script using the variables defined above
call "%bin%\Scripts\Launch.cmd" || goto ErrorLaunchCMD
goto Exit

:: Functions ::
:CheckFlags
rem Loops through all arguments to check for accepted flags
set DEBUG=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on & set "DEBUG=/DEBUG")
)
@exit /b 0

:FindBin
rem Checks the current directory and all parents for the ".bin" folder
rem NOTE: Has not been tested for UNC paths
set bin=
pushd "%~dp0"
:FindBinInner
if exist ".bin" (goto FindBinDone)
if "%~d0\" == "%cd%" (popd & @exit /b 1)
cd ..
goto FindBinInner
:FindBinDone
set "bin=%cd%\.bin"
set "cbin=%cd%\.cbin"
popd
@exit /b 0

:SetTitle
rem Sets title using KIT_NAME_FULL from settings\main.py
set "SETTINGS=%bin%\Scripts\settings\main.py"
for /f "tokens=* usebackq" %%f in (`findstr KIT_NAME_FULL %SETTINGS%`) do (
    set "_v=%%f"
    set "_v=!_v:*'=!"
    set "KIT_NAME_FULL=!_v:~0,-1!"
)
set "window_title=%*"
if not defined window_title set "window_title=Launcher"
set "window_title=%KIT_NAME_FULL%: %window_title%"
title %window_title%
@exit /b 0

:: Errors ::
:ErrorLaunchCMD
echo.
echo ERROR: Launch.cmd did not run correctly. Try using the /DEBUG flag?
goto Abort

:ErrorLaunchCMDMissing
echo.
echo ERROR: Launch.cmd script not found.
goto Abort

:ErrorNoBin
echo.
echo ERROR: ".bin" folder not found.
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