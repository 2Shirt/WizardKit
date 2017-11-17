@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
echo Waiting for software installation to finish...
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\_Drivers" "SerialNumberDetectionTool.exe" "" /admin /wait
start "" "http://us.acer.com/ac/en/US/content/drivers"