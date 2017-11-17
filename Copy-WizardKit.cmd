@echo off

:Flags
set silent=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
title Wizard Kit: Tools Copier
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
rem Set %client_dir%
call "%bin%\Scripts\init_client_dir.cmd"
pushd "%bin%\.."
set "source=%cd%"
set "dest=%client_dir%\Tools"

:CopyFiles
echo Copying data...
rem .bin
start "" /wait "%fastcopy%" %fastcopy_args% /exclude="\_Drivers\SDI\" "%bin%\*" /to="%dest%\.bin\"

rem RKill links
pushd "!dest!\.bin\RKill"
mklink /h explorer.exe RKill.exe >nul 2>&1
mklink /h iExplore.exe RKill.exe >nul 2>&1
mklink /h RKill.com RKill.exe >nul 2>&1
mklink /h RKill.scr RKill.exe >nul 2>&1
mklink /h uSeRiNiT.exe RKill.exe >nul 2>&1
mklink /h WiNlOgOn.exe RKill.exe >nul 2>&1
popd

rem Everything else
start "" /wait "%fastcopy%" %fastcopy_args% /exclude="\.bin\;\.git\;\Data Recovery\;\Copy-WizardKit.cmd;\Drivers\Auto Detect - SDI.cmd" "%source%" /to="%dest%\"

:OpenFolder
start "" explorer "!dest!"
goto Done

:ErrorNoBin
popd
echo ERROR: ".bin" folder not found..
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
