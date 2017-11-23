:: Wizard Kit: Copy Kit ::
@echo off

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Tools Copier
color 1b
echo Initializing...
call :CheckFlags %*
call :FindBin
call :SetTitle Tools Copier

:SetVariables
rem Set variables using settings\main.py file
set "SETTINGS=%bin%\Scripts\settings\main.py"
for %%v in (ARCHIVE_PASSWORD KIT_NAME_FULL) do (
    set "var=%%v"
    for /f "tokens=* usebackq" %%f in (`findstr "!var!=" %SETTINGS%`) do (
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
if %ARCH% equ 64 (
    set "SEVEN_ZIP=%bin%\7-Zip\7za64.exe"
    set "CON=%bin%\ConEmu\ConEmu64.exe"
    set "FASTCOPY=%bin%\FastCopy\FastCopy64.exe"
)
set "fastcopy_args=/cmd=diff /no_ui /auto_close"
rem Set %client_dir%
call "%bin%\Scripts\init_client_dir.cmd"
pushd "%bin%\.."
set "source=%cd%"
popd
set "dest=%client_dir%\Tools"

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
:CopyBin
echo Copying .bin...
mkdir "%dest%\.bin" >nul 2>&1
attrib +h "%dest%\.bin"
set _sources="%bin%\7-Zip"
set _sources=%_sources% "%bin%\ConEmu"
set _sources=%_sources% "%bin%\FastCopy"
set _sources=%_sources% "%bin%\HWiNFO"
set _sources=%_sources% "%bin%\Python"
set _sources=%_sources% "%bin%\Scripts"
start "" /wait "%fastcopy%" %fastcopy_args% %_sources% /to="%dest%\.bin\"

:CopyCBin
echo Copying .cbin...
mkdir "%dest%\.cbin" >nul 2>&1
attrib +h "%dest%\.cbin"
start "" /wait "%fastcopy%" %fastcopy_args% %cbin%\* /to="%dest%\.cbin\"

:CopyMainData
echo Copying Main Kit...
set _sources="%source%\Data Transfers"
set _sources=%_sources% "%source%\Diagnostics"
set _sources=%_sources% "%source%\Drivers"
set _sources=%_sources% "%source%\Installers"
set _sources=%_sources% "%source%\Misc"
set _sources=%_sources% "%source%\Repairs"
set _sources=%_sources% "%source%\Uninstallers"
set _sources=%_sources% "%source%\Activate Windows.cmd"
set _sources=%_sources% "%source%\Enter SafeMode.cmd"
set _sources=%_sources% "%source%\Exit SafeMode.cmd"
set _sources=%_sources% "%source%\LICENSE.txt"
set _sources=%_sources% "%source%\README.md"
set _sources=%_sources% "%source%\System Checklist.cmd"
set _sources=%_sources% "%source%\System Diagnostics.cmd"
set _sources=%_sources% "%source%\User Checklist.cmd"
start "" /wait "%fastcopy%" %fastcopy_args% /exclude="Snappy Driver Installer.cmd;*.exe" %_sources% /to="%dest%\"
start "" /wait "%fastcopy%" %fastcopy_args% "%source%\Installers\Extras\Office\Adobe Reader DC.exe" /to="%dest%\Installers\Extras\Office\"

:Ninite
echo Extracting Ninite installers...
"%SEVEN_ZIP%" x "%cbin%\_Ninite.7z" -aos -bso0 -bse0 -bsp0 -p%ARCHIVE_PASS% -o"%dest%\Installers\Extras" || goto Abort

:OpenFolder
start "" explorer "%dest%"
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
set "window_title=%*"
if not defined window_title set "window_title=Launcher"
set "window_title=%KIT_NAME_FULL%: %window_title%"
title %window_title%
@exit /b 0

:: Errors ::
:ErrorNoBin
echo.
echo ERROR: ".bin" folder not found.
goto Abort

:Abort
color 4e
echo Aborted.
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
