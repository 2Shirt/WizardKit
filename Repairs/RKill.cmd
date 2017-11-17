@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:FindBin
set bin= & pushd "%~dp0"
:FindBinInner
if exist ".bin" goto FindBinDone
if "%~d0\" == "%cd%" goto ErrorNoBin
cd .. & goto FindBinInner
:FindBinDone
set "bin=%cd%\.bin" & popd

:Init
setlocal EnableDelayedExpansion
color 1b
title Wizard Kit: Launcher

:CheckHardLinks
pushd "%bin%\RKill"
for %%r in (explorer.exe iExplore.exe RKill.com RKill.scr uSeRiNiT.exe WiNlOgOn.exe) do (
    if not exist "%%r" mklink /h %%r RKill.exe>nul 2>&1
)
popd

:CreateInfoDir
rem Create %client_dir%\Info\YYYY-MM-DD and set path as !log_dir!
call "%bin%\Scripts\init_client_dir.cmd" /Info

:RKill
echo Scanning system with RKill...
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "RKill\RKill.exe" "-l !log_dir!\rkill.log"
choice /c YA /d A /t 300 /m "Did RKill run correctly? Press Y for Yes, A to run Alternative."
if %errorlevel% equ 0 goto Abort
if %errorlevel% equ 1 goto Done
if %errorlevel% equ 2 goto RKillAlt

:RKillAlt
echo Scanning system with RKill...
set "prog=RKill\explorer.exe"
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "RKill\explorer.exe" "-l !log_dir!\rkill.log"
choice /c YM /d M /t 300 /m "Did RKill run correctly? Press Y for Yes, M to run manually."
if %errorlevel% equ 0 goto Abort
if %errorlevel% equ 1 goto Done
if %errorlevel% equ 2 goto RKillManual

:RKillManual
call "%bin%\Scripts\Launch.cmd" Program "%bin%\Explorer++" "Explorer++.exe" "%cd%\RKill"
goto Done

:Abort
color 4e
echo.
echo Aborted. Try running an alternate version manually.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:ErrorNoBin
popd
color 4e
echo ".bin" folder not found, aborting script.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:Done
color
endlocal
goto Exit

:Exit
goto Exit
