@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Console "%windir%\System32" "sfc.exe" "/scannow" "-new_console:c" /admin