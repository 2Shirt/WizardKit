@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\..\..\.bin\Scripts\Launch.cmd" Office "%~dp0\..\..\..\.bin\Scripts" "2007\Small Business 2007 (SP3)"
