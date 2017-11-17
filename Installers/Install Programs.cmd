@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:LaunchProgramSelection
call "%~dp0\..\.bin\Scripts\Launch.cmd" PSScript "%~dp0\..\.bin\Scripts" "install_programs.ps1" /admin