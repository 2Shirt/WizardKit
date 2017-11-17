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
rem Set %client_dir%
call "%bin%\Scripts\init_client_dir.cmd" /Quarantine
set "q_dir=%client_dir%\Quarantine\KVRT"
mkdir "%q_dir%">nul 2>&1

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%" "KVRT.exe" "-accepteula -d %q_dir% -processlevel 3 -dontcryptsupportinfo -fixednames"
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
