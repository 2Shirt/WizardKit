:: WizardKit: Wrapper for launching programs and scripts.
::
:: Some features:
::   * If the OS is 64-bit then the WorkingDir is scanned for a 64-bit version of the programs
::   * Allows for centralized terminal emulation settings management
::   * Allows for smaller "launcher" scripts to be used as they will rely on this script.

@echo off
if defined DEBUG (@echo on)

:Init
setlocal EnableDelayedExpansion
title WizardKit: Launcher
pushd "%~dp0"
call :FindBin
call :DeQuote L_ITEM
call :DeQuote L_PATH
call :DeQuote L_TYPE

:SetVariables
rem Set variables using settings\main.py file
set "SETTINGS=%bin%\Scripts\wk\cfg\main.py"
for %%v in (ARCHIVE_PASSWORD KIT_NAME_FULL OFFICE_SERVER_IP QUICKBOOKS_SERVER_IP) do (
  set "var=%%v"
  for /f "tokens=* usebackq" %%f in (`findstr "!var!=" "%SETTINGS%"`) do (
    set "_v=%%f"
    set "_v=!_v:*'=!"
    set "%%v=!_v:~0,-1!"
  )
)
rem Set ARCH to 32 as a gross assumption and check for x86_64 status
set ARCH=32
if /i "%PROCESSOR_ARCHITECTURE%" == "AMD64" set "ARCH=64"
set "SEVEN_ZIP=%bin%\7-Zip\7za.exe"
set "CON=%bin%\ConEmu\ConEmu.exe"
set "FASTCOPY=%bin%\FastCopy\FastCopy.exe"
set "POWERSHELL=%systemroot%\system32\WindowsPowerShell\v1.0\powershell.exe"
set "PYTHON=%bin%\Python\x32\python.exe"
if %ARCH% equ 64 (
  set "SEVEN_ZIP=%bin%\7-Zip\7za64.exe"
  set "CON=%bin%\ConEmu\ConEmu64.exe"
  set "FASTCOPY=%bin%\FastCopy\FastCopy64.exe"
  set "PYTHON=%bin%\Python\x64\python.exe"
)

:UpdateTitle
rem Sets title using KIT_NAME_FULL from settings\main.py (unless %window_title% already set)
if defined window_title (
  title %window_title%
) else (
  set "window_title=%*"
  if not defined window_title set "window_title=Launcher"
  set "window_title=%KIT_NAME_FULL%: %window_title%"
  title %window_title%
)

:CheckUsage
rem Check for empty passed variables
if not defined L_TYPE (goto Usage)
if not defined L_PATH (goto Usage)
if not defined L_ITEM (goto Usage)
rem Assume if not "True" then False (i.e. undefine variable)
if /i not "%L_ELEV%" == "True" (set "L_ELEV=")
if /i not "%L_NCMD%" == "True" (set "L_NCMD=")
if /i not "%L__CLI%" == "True" (set "L__CLI=")

:RelaunchInConEmu
set RELOAD_IN_CONEMU=True
if defined ConEmuBuild        set "RELOAD_IN_CONEMU="
if defined L_NCMD             set "RELOAD_IN_CONEMU="
if "%L_TYPE%" == "Executable" set "RELOAD_IN_CONEMU="
if "%L_TYPE%" == "PSScript"   set "RELOAD_IN_CONEMU="
if "%L_TYPE%" == "PyScript"   set "RELOAD_IN_CONEMU="

if defined RELOAD_IN_CONEMU (
  set "con_args=-new_console:n"
  rem If in DEBUG state then force ConEmu to stay open
  if defined DEBUG (set "con_args=!con_args! -new_console:c")
  start "" "%CON%" -run ""%~0" %*" !con_args! || goto ErrorUnknown
  exit /b 0
)

:CheckLaunchType
rem Jump to the selected launch type or show usage
if /i "%L_TYPE%" == "Executable"  (goto LaunchExecutable)
if /i "%L_TYPE%" == "Folder"      (goto LaunchFolder)
if /i "%L_TYPE%" == "Office"      (goto LaunchOffice)
if /i "%L_TYPE%" == "PSScript"    (goto LaunchPSScript)
if /i "%L_TYPE%" == "PyScript"    (goto LaunchPyScript)
if /i "%L_TYPE%" == "QuickBooks"  (goto LaunchQuickBooksSetup)
goto Usage

:LaunchExecutable
rem Prep
call :ExtractOrFindPath || goto ErrorProgramNotFound

rem Check for 64-bit prog (if running on 64-bit system)
set "prog=%_path%\%L_ITEM%"
if %ARCH% equ 64 (
  if exist "%_path%\%L_ITEM:.=64.%" set "prog=%_path%\%L_ITEM:.=64.%"
) else (
  if exist "%_path%\%L_ITEM:.=32.%" set "prog=%_path%\%L_ITEM:.=32.%"
)
if not exist "%prog%" goto ErrorProgramNotFound

rem Run
popd && pushd "%_path%"
if defined L__CLI goto LaunchExecutableCLI
if defined L_ELEV (
  goto LaunchExecutableElev
) else (
  goto LaunchExecutableUser
)

:LaunchExecutableCLI
rem Prep
set "con_args=-new_console:n"
if defined DEBUG (set "con_args=%con_args% -new_console:c")
if defined L_ELEV (set "con_args=%con_args% -new_console:a")

rem Run
start "" "%CON%" -run "%prog%" %L_ARGS% %con_args% || goto ErrorUnknown
goto Exit

:LaunchExecutableElev
rem Prep
call :DeQuote prog
call :DeQuote L_ARGS

rem Create VB script
mkdir "%bin%\tmp" 2>nul
echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
echo UAC.ShellExecute "%prog%", "%L_ARGS%", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"

rem Run
"%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
goto Exit

:LaunchExecutableUser
rem Run
start "" "%prog%" %L_ARGS% || goto ErrorUnknown
goto Exit

:LaunchFolder
rem Prep
call :ExtractOrFindPath || goto ErrorProgramNotFound

rem Run
start "" "explorer.exe" "%_path%" || goto ErrorUnknown
goto Exit

:LaunchOffice
call "%bin%\Scripts\init_client_dir.cmd" /Office
set "_odt=False"
if %L_PATH% equ 2016 (set "_odt=True")
if %L_PATH% equ 2019 (set "_odt=True")
if "%_odt%" == "True" (
  goto LaunchOfficeODT
) else (
  goto LaunchOfficeSetup
)

:LaunchOfficeODT
rem Prep
set "args=-aoa -bso0 -bse0 -bsp0 -p%ARCHIVE_PASSWORD%"
set "config=%L_ITEM%"
set "dest=%client_dir%\Office\ODT"
set "odt_exe=setup.exe"
set "source=%cbin%\_Office.7z"

rem Extract
if not exist "%source%" (goto ErrorODTSourceNotFound)
"%SEVEN_ZIP%" e "%source%" %args% -o"%dest%" %odt_exe% %config% || exit /b 1
"%systemroot%\System32\ping.exe" -n 2 127.0.0.1>nul

rem Verify
if not exist "%dest%\setup.exe" (goto ErrorODTSourceNotFound)
if not exist "%dest%\%config%" (goto ErrorODTSourceNotFound)
pushd "%dest%"

rem Run
rem # The line below jumps to ErrorUnknown even when it runs correctly??
rem start "" "setup.exe" /configure %L_ITEM% || popd & goto ErrorUnknown
rem # Going to assume it extracted correctly and blindly start setup.exe
start "" "setup.exe" /configure %config%
popd
goto Exit

:LaunchOfficeSetup
rem Prep
set "fastcopy_args=/cmd=diff /no_ui /auto_close"
set "product=%L_PATH%\%L_ITEM%"
set "product_name=%L_ITEM%"
call :GetBasename product_name || goto ErrorBasename
set "source=\\%OFFICE_SERVER_IP%\Office\%product%"
set "dest=%client_dir%\Office"

rem Verify
if not exist "%source%" (goto ErrorOfficeSourceNotFound)

rem Copy
echo Copying setup file(s) for %product_name%...
start "" /wait "%FASTCOPY%" %fastcopy_args% "%source%" /to="%dest%\"

rem Run
if exist "%dest%\%product_name%\setup.exe" (
  start "" "%dest%\%product_name%\setup.exe" || goto ErrorUnknown
) else if "%product_name:~-3,3%" == "exe" (
  start "" "%dest%\%product_name%" || goto ErrorUnknown
) else if "%product_name:~-3,3%" == "msi" (
  start "" "%dest%\%product_name%" || goto ErrorUnknown
) else (
  rem Office source not supported by this script
  goto ErrorOfficeUnsupported
)
goto Exit

:LaunchPSScript
rem Prep
call :ExtractOrFindPath || goto ErrorProgramNotFound
set "script=%_path%\%L_ITEM%"
set "ps_args=-ExecutionPolicy Bypass -NoProfile"

rem Verify
if not exist "%script%" goto ErrorScriptNotFound

rem Run
popd && pushd "%_path%"
if defined L_ELEV (
  goto LaunchPSScriptElev
) else (
  goto LaunchPSScriptUser
)

:LaunchPSScriptElev
rem Prep
call :DeQuote script

rem Create VB script
mkdir "%bin%\tmp" 2>nul
echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
if defined L_NCMD (
  rem use Powershell's window instead of %CON%
  echo UAC.ShellExecute "%POWERSHELL%", "%ps_args% -File "%script%"", "", "runas", 3 >> "%bin%\tmp\Elevate.vbs"
) else (
  echo UAC.ShellExecute "%CON%", "-run %POWERSHELL% %ps_args% -File "%script%" -new_console:n", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"
)

rem Run
"%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
goto Exit

:LaunchPSScriptUser
rem Run
if defined L_NCMD (
  start "" "%POWERSHELL%" %ps_args% -File "%script%" || goto ErrorUnknown
) else (
  start "" "%CON%" -run "%POWERSHELL%" %ps_args% -File "%script%" -new_console:n || goto ErrorUnknown
)
goto Exit

:LaunchPyScript
rem Prep
call :ExtractOrFindPath || goto ErrorProgramNotFound
set "script=%_path%\%L_ITEM%"

rem Verify
"%PYTHON%" --version >nul || goto ErrorPythonUnsupported
if not exist "%script%" goto ErrorScriptNotFound

rem Run
if defined L_ELEV (
  goto LaunchPyScriptElev
) else (
  goto LaunchPyScriptUser
)

:LaunchPyScriptElev
rem Prep
call :DeQuote script

rem Create VB script
mkdir "%bin%\tmp" 2>nul
echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
if defined L_NCMD (
  echo UAC.ShellExecute "%PYTHON%", """%script%"" %L_ARGS%", "", "runas", 3 >> "%bin%\tmp\Elevate.vbs"
) else (
  echo UAC.ShellExecute "%CON%", "-run ""%PYTHON%"" ""%script%"" %L_ARGS% -new_console:n", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"
)

rem Run
"%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
goto Exit

:LaunchPyScriptUser
if defined L_NCMD (
  start "" "%PYTHON%" "%script%" %L_ARGS% || goto ErrorUnknown
) else (
  start "" "%CON%" -run "%PYTHON%" "%script%" %L_ARGS% -new_console:n || goto ErrorUnknown
)
goto Exit

:LaunchQuickBooksSetup
rem Prep
call "%bin%\Scripts\init_client_dir.cmd" /QuickBooks
set "fastcopy_args=/cmd=diff /no_ui /auto_close"
set "product=%L_PATH%\%L_ITEM%"
set "product_name=%L_ITEM%"
call :GetBasename product_name || goto ErrorBasename
set "source=\\%QUICKBOOKS_SERVER_IP%\QuickBooks\%product%"
set "dest=%client_dir%\QuickBooks"

rem Verify
if not exist "%source%" (goto ErrorQuickBooksSourceNotFound)

rem Copy
echo Copying setup file(s) for %L_ITEM%...
start "" /wait "%FASTCOPY%" %fastcopy_args% "%source%" /to="%dest%\"

rem Run
if exist "%dest%\%product_name%\Setup.exe" (
  pushd "%dest%\%product_name%"
  start "" "%dest%\%product_name%\Setup.exe" || goto ErrorUnknown
  popd
) else (
  rem QuickBooks source not supported by this script
  goto ErrorQuickBooksUnsupported
)
goto Exit

:Usage
echo.
echo.Usage (via defined variables):
echo.   L_TYPE      L_PATH       L_ITEM   L_ARGS
echo.   Executable  Working Dir  Program  Args   [L_7ZIP] [L_ELEV] [L__CLI]
echo.   Folder    Folder     '.'                 [L_7ZIP]
echo.   Office    Year       Product             [L_7ZIP]
echo.   PSScript  Scripts    Script              [L_7ZIP] [L_ELEV] [L_NCMD]
echo.   PyScript  Scripts    Script       Args   [L_7ZIP] [L_ELEV] [L_NCMD]
echo.   QuickBooks  Year     Product             [L_7ZIP]
echo.
echo.L_7ZIP:  Extra arguments for 7-Zip (in the :ExtractCBin label)
echo.L_ELEV:  Elevate to run as Admin
echo.L_NCMD:  Do not run script inside ConEmu (i.e. use the native window)
echo.L__CLI:  Run executable in ConEmu
echo.
goto Abort

:: Functions ::
:DeQuote
rem Code taken from http://ss64.com/nt/syntax-dequote.html
if not defined %1 (@exit /b 1)
for /f "delims=" %%a in ('echo %%%1%%') do set %1=%%~a
@exit /b 0

:ExtractCBin
rem Extract %cbin% archive into %bin%
echo Extracting "%L_PATH%"...
set "source=%cbin%\%L_PATH%.7z"
set "dest=%bin%\%L_PATH%"
set "args=-aos -bso0 -bse0 -bsp0 -p%ARCHIVE_PASSWORD%"
if defined DEBUG (set "args=-aos -p%ARCHIVE_PASSWORD%")
"%SEVEN_ZIP%" x "%source%" %args% -o"%dest%" %L_7ZIP% || exit /b 1
ping.exe -n 2 127.0.0.1>nul
exit /b 0

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

:GetBasename
rem Loop over passed variable to remove all text left of the last '\' character
rem NOTE: This function should be called as 'call :GetBasename VarName || goto ErrorBasename' to catch variables that become empty.
for /f "delims=" %%a in ('echo %%%1%%') do (set "_tmp=%%~a")
:GetBasenameInner
set "_tmp=%_tmp:*\=%"
if not defined _tmp (@exit /b 1)
if not "%_tmp%" == "%_tmp:*\=%" (goto GetBasenameInner)
:GetBasenameDone
set "%1=%_tmp%"
@exit /b 0

:ExtractOrFindPath
rem Test L_PATH in the following order:
rem    1: %cbin%\L_PATH.7z (which will be extracted to %bin%\L_PATH)
rem    2: %bin%\L_PATH
rem    3. %L_PATH%     (i.e. treat L_PATH as an absolute path)
rem NOTE: This function should be called as 'call :ExtractOrFindPath || goto ErrorProgramNotFound' to catch invalid paths.
set _path=
if exist "%cbin%\%L_PATH%.7z" (
  call :ExtractCBin
) else if exist "%cbin%\%L_PATH%\%L_ITEM:~0,-4%.7z" (
  call :ExtractCBin
)
if exist "%bin%\%L_PATH%" (set "_path=%bin%\%L_PATH%")
if not defined _path (set "_path=%L_PATH%")
rem Raise error if path is still not available
if not exist "%_path%" (exit /b 1)
exit /b 0

:: Errors ::
:ErrorBasename
echo.
echo ERROR: GetBasename resulted in an empty variable.
goto Abort

:ErrorNoBin
echo.
echo ERROR: ".bin" folder not found.
goto Abort

:ErrorODTSourceNotFound
echo.
echo ERROR: Office Deployment Tool source not found.
goto Abort

:ErrorOfficeSourceNotFound
echo.
echo ERROR: Office source "%L_ITEM%" not found.
goto Abort

:ErrorOfficeUnsupported
rem Source is not an executable nor is a folder with a setup.exe file inside. Open explorer to local setup file(s) instead.
echo.
echo ERROR: Office version not supported by this script.
start "" "explorer.exe" "%client_dir%\Office"
goto Abort

:ErrorPythonUnsupported
rem The Windows installation lacks Windows update KB2999226 needed to run Python
echo.
echo ERROR: Failed to run Python, try installing Windows update KB2999226.
echo NOTE: That update is from October 2015 so this system is SEVERELY outdated
if exist "%bin%\..\Installers\Extras\Windows Updates" (
  start "" "explorer.exe" "%bin%\..\Installers\Extras\Windows Updates"
)
goto Abort

:ErrorQuickBooksSourceNotFound
echo.
echo ERROR: QuickBooks source "%L_ITEM%" not found.
goto Abort

:ErrorQuickBooksUnsupported
rem Source is not an executable nor is a folder with a setup.exe file inside. Open explorer to local setup file(s) instead.
echo.
echo ERROR: QuickBooks version not supported by this script.
start "" "explorer.exe" "%client_dir%\QuickBooks"
goto Abort

:ErrorProgramNotFound
echo.
echo ERROR: Program "%prog%" not found.
goto Abort

:ErrorScriptNotFound
echo.
echo ERROR: Script "%script%" not found.
goto Abort

:ErrorUnknown
echo.
echo ERROR: Unknown error encountered.
goto Abort

:Abort
rem Handle color theme for both the native console and ConEmu
if defined ConEmuBuild (
  color c4
) else (
  color 4e
)
echo Aborted.
echo.
echo DETAILS: L_TYPE: %L_TYPE%
echo.         L_PATH: %L_PATH%
echo.         L_ITEM: %L_ITEM%
echo.         L_ARGS: %L_ARGS%
echo.         L_7ZIP: %L_7ZIP%
echo.         L_ELEV: %L_ELEV%
echo.         L_NCMD: %L_NCMD%
echo.         L__CLI: %L__CLI%
echo.         CON:    %CON%
echo.         DEBUG:  %DEBUG%
echo.         PYTHON: %PYTHON%
echo Press any key to exit...
pause>nul
rem reset color and reset errorlevel to 0
rem NOTE: This is done to avoid causing a ErrorLaunchCMD in the launcher.cmd
color 07
goto Exit

:: Cleanup and exit ::
:Exit
popd
endlocal
exit /b %errorlevel%
