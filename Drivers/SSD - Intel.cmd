@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\_Drivers" "Intel SSD Toolbox - v3.3.4.exe" ""