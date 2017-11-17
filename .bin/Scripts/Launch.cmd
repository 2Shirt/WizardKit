:: Wizard Kit: Wrapper for launching programs and scripts.
::
:: Some features:
::   * If the OS is 64-bit then the WorkingDir is scanned for a 64-bit version of the programs
::   * Allows for centralized terminal emulation settings management
::   * Allows for smaller "launcher" scripts to be used as they will rely on this script.

@echo off
if defined DEBUG (@echo on)

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Launcher
pushd "%~dp0"
call :FindBin
call :DeQuote L_ITEM
call :DeQuote L_PATH
call :DeQuote L_TYPE

:SetVariables
set "ARCHIVE_PASS=Abracadabra"
set "OFFICE_SERVER=10.0.0.10"
set "QUICKBOOKS_SERVER=10.0.0.10"
rem Set ARCH to 32 as a gross assumption and check for x86_64 status
set ARCH=32
if /i "%PROCESSOR_ARCHITECTURE%" == "AMD64" set "ARCH=64"
set "SEVEN_ZIP=%bin%\7-Zip\7za.exe"
set "CON=%bin%\ConEmu\ConEmu.exe"
set "FASTCOPY=%bin%\FastCopy\FastCopy.exe"
set "PYTHON=%bin%\Python\x32\python.exe"
if %ARCH% equ 64 (
    set "SEVEN_ZIP=%bin%\7-Zip\7za64.exe"
    set "CON=%bin%\ConEmu\ConEmu64.exe"
    set "FASTCOPY=%bin%\FastCopy\FastCopy64.exe"
    set "PYTHON=%bin%\Python\x64\python.exe"
)

:CheckUsage
rem Check for empty passed variables
if not defined L_TYPE (goto Usage)
if not defined L_PATH (goto Usage)
if not defined L_ITEM (goto Usage)
rem Assume if not "True" then False (i.e. undefine variable)
if /i not "%L_CHCK%" == "True" (set "L_CHCK=")
if /i not "%L_ELEV%" == "True" (set "L_ELEV=")
if /i not "%L_NCMD%" == "True" (set "L_NCMD=")
if /i not "%L_WAIT%" == "True" (set "L_WAIT=")

:RelaunchInConEmu
if not defined IN_CONEMU (
    if not defined L_NCMD (
        set "con_args=-new_console:n"
        rem If in DEBUG state then force ConEmu to stay open
        if defined DEBUG (set "con_args=!con_args! -new_console:c")
        set IN_CONEMU=True
        start "" "%CON%" -run ""%~0" %*" !con_args! || goto ErrorUnknown
        exit /b 0
    )
)

:CheckLaunchType
rem Jump to the selected launch type or show usage
if /i "%L_TYPE%" == "Console"       (goto LaunchConsole)
if /i "%L_TYPE%" == "Folder"        (goto LaunchFolder)
if /i "%L_TYPE%" == "Office"        (goto LaunchOfficeSetup)
if /i "%L_TYPE%" == "QuickBooks"    (goto LaunchQuickBooksSetup)
if /i "%L_TYPE%" == "Program"       (goto LaunchProgram)
if /i "%L_TYPE%" == "PSScript"      (goto LaunchPSScript)
if /i "%L_TYPE%" == "PyScript"      (goto LaunchPyScript)
if /i "%L_TYPE%" == "PywScript"     (goto LaunchPywScript)
goto Usage

:LaunchConsole
rem Check for a 64-bit version and set args
set "con_args=-new_console:n"
if defined DEBUG (set "con_args=%con_args% -new_console:c")
if defined L_ELEV (set "con_args=%con_args% -new_console:a")
rem Test L_PATH and set %_path%
call :TestPath || goto ErrorProgramNotFound
rem Check for 64-bit prog (if running on 64-bit system)
set "prog=%_path%\%L_ITEM%"
if %ARCH% equ 64 (
    if exist "%_path%\%L_ITEM:.=64.%" set "prog=%_path%\%L_ITEM:.=64.%"
)
if not exist "%prog%" goto ErrorProgramNotFound
popd && pushd "%_path%"
rem Run program in console emulator %CON% and catch error(s)
start "" "%CON%" -run "%prog%" %L_ARGS% %con_args% || goto ErrorUnknown
goto Exit

:LaunchFolder
rem Test L_PATH and set %_path% (extracts archive in necessary)
call :TestPath || goto ErrorProgramNotFound
start "" "explorer.exe" "%_path%" || goto ErrorUnknown
goto Exit

:LaunchOfficeSetup
rem set args and copy setup files to system
rem NOTE: init_client_dir.cmd sets %client_dir% and creates %SystemDrive%\WK\Office folder
call "%bin%\Scripts\init_client_dir.cmd" /Office
echo Copying setup file(s) for %L_ITEM%...
rem NOTE: If L_PATH == "2013" or "2016" extract the ODT setup/xml, otherwise copy from OFFICE_SERVER
set "_odt=False"
if %L_PATH% equ 2013 (set "_odt=True")
if %L_PATH% equ 2016 (set "_odt=True")
if "%_odt%" == "True" (
    rem extract setup/xml and start installation
    set "source=%L_PATH%\setup.exe"
    set "dest=%client_dir%\Office\%L_PATH%"
    "%SEVEN_ZIP%" e "%cbin%\_Office.7z" -aoa -bso0 -bse0 -p%ARCHIVE_PASS% -o"!dest!" !source! !L_ITEM! || exit /b 1
    "%systemroot%\System32\ping.exe" -n 2 127.0.0.1>nul
    if not exist "!dest!\setup.exe" (goto ErrorOfficeSourceNotFound)
    if not exist "!dest!\!L_ITEM!" (goto ErrorOfficeSourceNotFound)
    pushd "!dest!"
    rem # The line below jumps to ErrorUnknown even though setup.exe is run correctly??
    rem start "" "setup.exe" /configure !L_ITEM! || popd & goto ErrorUnknown
    rem # Going to assume it extracted correctly and blindly start setup.exe
    start "" "setup.exe" /configure !L_ITEM!
    popd
) else (
    rem copy setup files from OFFICE_SERVER
    set "fastcopy_args=/cmd=diff /no_ui /auto_close"
    set "product=%L_PATH%\%L_ITEM%"
    set "product_name=%L_ITEM%"
    call :GetBasename product_name || goto ErrorBasename
    set "source=\\%OFFICE_SERVER%\Office\!product!"
    set "dest=%client_dir%\Office"
    rem Verify source
    if not exist "!source!" (goto ErrorOfficeSourceNotFound)
    rem Copy setup file(s) to system
    start "" /wait "%FASTCOPY%" !fastcopy_args! "!source!" /to="!dest!\"
    rem Run setup
    if exist "!dest!\!product_name!\setup.exe" (
        start "" "!dest!\!product_name!\setup.exe" || goto ErrorUnknown
    ) else if "!product_name:~-3,3!" == "exe" (
        start "" "!dest!\!product_name!" || goto ErrorUnknown
    ) else if "!product_name:~-3,3!" == "msi" (
        start "" "!dest!\!product_name!" || goto ErrorUnknown
    ) else (
        rem Office source not supported by this script
        goto ErrorOfficeUnsupported
    )
)
goto Exit

:LaunchQuickBooksSetup
rem set args and copy setup files to system
rem NOTE: init_client_dir.cmd sets %client_dir% and creates %SystemDrive%\WK\QuickBooks folder
call "%bin%\Scripts\init_client_dir.cmd" /QuickBooks
echo Copying setup file(s) for %L_ITEM%...
rem copy setup files from QUICKBOOKS_SERVER
set "fastcopy_args=/cmd=diff /no_ui /auto_close"
set "product=%L_PATH%\%L_ITEM%"
set "product_name=%L_ITEM%"
call :GetBasename product_name || goto ErrorBasename
set "source=\\%QUICKBOOKS_SERVER%\QuickBooks\!product!"
set "dest=%client_dir%\QuickBooks"
rem Verify source
if not exist "!source!" (goto ErrorQuickBooksSourceNotFound)
rem Copy setup file(s) to system
start "" /wait "%FASTCOPY%" !fastcopy_args! "!source!" /to="!dest!\"
rem Run setup
if exist "!dest!\!product_name!\Setup.exe" (
    pushd "!dest!\!product_name!"
    start "" "!dest!\!product_name!\Setup.exe" || goto ErrorUnknown
    popd
) else (
    rem QuickBooks source not supported by this script
    goto ErrorQuickBooksUnsupported
)
goto Exit

:LaunchProgram
rem Test L_PATH and set %_path%
call :TestPath || goto ErrorProgramNotFound
rem Check for 64-bit prog (if running on 64-bit system)
set "prog=%_path%\%L_ITEM%"
if %ARCH% equ 64 (
    if exist "%_path%\%L_ITEM:.=64.%" set "prog=%_path%\%L_ITEM:.=64.%"
)
if not exist "%prog%" goto ErrorProgramNotFound
popd && pushd "%_path%"
rem Run program and catch error(s)
if defined L_ELEV (
    call :DeQuote prog
    call :DeQuote L_ARGS
    rem Create a temporary VB script to elevate the specified program
    mkdir "%bin%\tmp" 2>nul
    echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
    echo UAC.ShellExecute "!prog!", "!L_ARGS!", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"
    "%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
) else (
    if defined L_WAIT (set "wait=/wait")
    start "" %wait% "%prog%" %L_ARGS% || goto ErrorUnknown
)
goto Exit

:LaunchPSScript
rem Test L_PATH and set %_path%
rem NOTE: This should always result in path=%bin%\Scripts. Exceptions are unsupported.
call :TestPath || goto ErrorProgramNotFound
rem Set args
set "script=%_path%\%L_ITEM%"
set "ps_args=-ExecutionPolicy Bypass -File "%script%" -NoProfile"
if defined L_ELEV (set "ps_args=%ps_args% -new_console:a -new_console:n")
if defined L_WAIT (set "ps_args=%ps_args% -Wait")
if not exist "%script%" goto ErrorScriptNotFound
rem Run program and catch error(s)
start "" "%CON%" -run %systemroot%\system32\WindowsPowerShell\v1.0\powershell.exe %ps_args% || goto ErrorUnknown
goto Exit

:LaunchPyScript
rem Test L_PATH and set %_path%
rem NOTE: This should always result in path=%bin%\Scripts. Exceptions are unsupported.
call :TestPath || goto ErrorProgramNotFound
rem Set args
set "script=%_path%\%L_ITEM%"
set "py_args=-new_console:n"
if not exist "%script%" goto ErrorScriptNotFound
if defined L_ELEV (
    call :DeQuote script
    rem Create a temporary VB script to elevate the specified program
    mkdir "%bin%\tmp" 2>nul
    echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
    echo UAC.ShellExecute "%CON%", "-run %PYTHON% !script! %py_args%", "", "runas", 1 >> "%bin%\tmp\Elevate.vbs"
    "%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
) else (
    start "" "%CON%" -run "%PYTHON%" "%script%" %py_args% || goto ErrorUnknown
)
goto Exit

:LaunchPywScript
rem Test L_PATH and set %_path%
rem NOTE: This should always result in path=%bin%\Scripts. Exceptions are unsupported.
call :TestPath || goto ErrorProgramNotFound
rem Set args
set "script=%_path%\%L_ITEM%"
if not exist "%script%" goto ErrorScriptNotFound
if defined L_ELEV (
    call :DeQuote script
    rem Create a temporary VB script to elevate the specified program
    mkdir "%bin%\tmp" 2>nul
    echo Set UAC = CreateObject^("Shell.Application"^) > "%bin%\tmp\Elevate.vbs"
    echo UAC.ShellExecute "%PYTHON%", "!script!", "", "runas", 3 >> "%bin%\tmp\Elevate.vbs"
    "%systemroot%\System32\cscript.exe" //nologo "%bin%\tmp\Elevate.vbs" || goto ErrorUnknown
) else (
    start "" "%PYTHON%" "%script%" /max || goto ErrorUnknown
)
goto Exit

:Usage
echo.
echo.Usage (via defined variables):
echo.   L_TYPE      L_PATH       L_ITEM   L_ARGS
echo.   Console     Working Dir  Program  Args   [L_CHECK] [L_ELEV] [L_NCMD] [L_WAIT]
echo.   Folder      Folder       '.'             [L_CHECK]          [L_NCMD]
echo.   Office      Year         Product         [L_CHECK]          [L_NCMD]
echo.   QuickBooks  Year         Product         [L_CHECK]          [L_NCMD]
echo.   Program     Working Dir  Program  Args   [L_CHECK] [L_ELEV] [L_NCMD] [L_WAIT]
echo.   PSScript    Scripts      Script          [L_CHECK] [L_ELEV] [L_NCMD]
echo.   PyScript    Scripts      Script          [L_CHECK] [L_ELEV] [L_NCMD]
echo.   PywScript   Scripts      Script          [L_CHECK] [L_ELEV] [L_NCMD]
echo.
echo.   NOTE: PywScript uses Python's window instead of %CON%
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
echo Extracting "%L_ITEM%"...
if exist "%cbin%\%L_PATH%\%L_ITEM:~0,-4%.7z" (
    "%SEVEN_ZIP%" x "%cbin%\%L_PATH%\%L_ITEM:~0,-4%.7z" -aos -bso0 -bse0 -p%ARCHIVE_PASS% -o"%bin%\%L_PATH%" %L_7ZIP% || exit /b 1
) else (
    "%SEVEN_ZIP%" x "%cbin%\%L_PATH%.7z" -aos -bso0 -bse0 -p%ARCHIVE_PASS% -o"%bin%\%L_PATH%" %L_7ZIP% || exit /b 1
)
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

:TestPath
rem Test L_PATH in the following order:
rem      1: %cbin%\L_PATH.7z (which will be extracted to %bin%\L_PATH)
rem      2: %bin%\L_PATH
rem      3. %L_PATH%         (i.e. treat L_PATH as an absolute path)
rem NOTE: This function should be called as 'call :TestPath || goto ErrorProgramNotFound' to catch invalid paths.
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
if defined L_NCMD (
    color 4e
) else (
    color c4
)
echo Aborted.
echo.
echo DETAILS: L_TYPE: %L_TYPE%
echo.         L_PATH: %L_PATH%
echo.         L_ITEM: %L_ITEM%
echo.         L_ARGS: %L_ARGS%
echo.         L_CHCK: %L_CHCK%
echo.         L_ELEV: %L_ELEV%
echo.         L_NCMD: %L_NCMD%
echo.         L_WAIT: %L_WAIT%
echo.         CON:    %CON%
echo.         DEBUG:  %DEBUG%
echo.         PYTHON: %PYTHON%
rem Pause script only if we want to catch the error AND only when using ConEmu
if defined L_CHCK (
    if not defined L_NCMD (
        echo Press any key to exit...
        pause>nul
    )
)
color
rem Set errorlevel to 1 by calling color incorrectly
color 00
goto Exit

:: Cleanup and exit ::
:Exit
popd
endlocal
exit /b %errorlevel%