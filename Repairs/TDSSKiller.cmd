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
rem Create %client_dir%\Info\YYYY-MM-DD and set path as %log_dir%
call "%bin%\Scripts\init_client_dir.cmd" /Info /Quarantine

:CreateQuarantineDir
set "q_dir=%client_dir%\Quarantine\TDSSKiller"
mkdir "%q_dir%">nul 2>&1

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "TDSSKiller.exe" "-l %log_dir%\TDSSKiller.log -qpath %q_dir% -accepteula -accepteulaksn -dcexact -tdlfs"
rem call "%bin%\Scripts\Launch.cmd" Program "%bin%" "TDSSKiller.exe" "-l %log_dir%\TDSSKiller.log -qpath %q_dir% -accepteula -accepteulaksn -dcexact -qsus -tdlfs"
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

:Exit
