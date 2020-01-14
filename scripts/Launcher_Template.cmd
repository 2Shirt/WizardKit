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

:Optional
:: This section is for any work that needs done before launching L_ITEM
rem EXTRA_CODE

:DefineLaunch
:: See %bin%\Scripts\Launch.cmd for details under :Usage label
set L_TYPE=
set L_PATH=
set L_ITEM=
set L_ARGS=
set L__CLI=
set L_7ZIP=
set L_ELEV=
set L_NCMD=

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
for /f "tokens=* usebackq" %%f in (`findstr KIT_NAME_FULL "%SETTINGS%"`) do (
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
