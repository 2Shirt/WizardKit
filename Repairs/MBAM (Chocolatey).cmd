@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:InstallMBAM
call "%~dp0\..\.bin\Scripts\Launch.cmd" PSScript "%~dp0\..\.bin\Scripts" "install_mbam.ps1" /admin
