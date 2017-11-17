@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\..\..\.bin\Scripts\Launch.cmd" Office "%~dp0\..\..\..\.bin\Scripts" "2013\Home and Student 2013"
