@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
color 1b
title WK Launcher
pushd %~dp0\..\.bin

:CheckHardLinks
pushd RKill
for %%r in (explorer.exe iExplore.exe RKill.com RKill.scr uSeRiNiT.exe WiNlOgOn.exe) do (
    if not exist "%%r" mklink /h %%r RKill.exe>nul 2>&1
)
popd

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as !log_dir!
call "%~dp0\..\.bin\Scripts\wk_info.cmd"

:RKill
echo Scanning system with RKill...
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "RKill\RKill.exe" "-l !log_dir!\rkill.log"
choice /c YA /d A /t 300 /m "Did RKill run correctly? Press Y for Yes, A to run Alternative."
if %errorlevel% equ 0 goto Abort
if %errorlevel% equ 1 goto Done
if %errorlevel% equ 2 goto RKillAlt

:RKillAlt
echo Scanning system with RKill...
set "prog=RKill\explorer.exe"
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "RKill\explorer.exe" "-l !log_dir!\rkill.log"
choice /c YM /d M /t 300 /m "Did RKill run correctly? Press Y for Yes, M to run manually."
if %errorlevel% equ 0 goto Abort
if %errorlevel% equ 1 goto Done
if %errorlevel% equ 2 goto RKillManual

:RKillManual
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\Explorer++" "Explorer++.exe" "%cd%\RKill"
goto Done

:Abort
color 4e
echo.
echo Aborted. Try running an alternate version manually.
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