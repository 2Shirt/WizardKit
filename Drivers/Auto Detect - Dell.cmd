@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
echo Waiting for software installation to finish...
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\_Drivers" "DellSystemDetectLauncher.exe" "" /admin /wait
start "" "http://www.dell.com/support/home/us/en/19/Eula/scan?sourcePage=J&scanType=TMC&loadSection=N&AppName=drivers&app=drivers"