@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\.bin\Scripts\Launch.cmd" PSScript "%~dp0\.bin\Scripts" "exit_safemode.ps1" /admin