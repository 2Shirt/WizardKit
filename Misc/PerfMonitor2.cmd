@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\PerfMonitor2" "PerfMonitor2.exe" ""