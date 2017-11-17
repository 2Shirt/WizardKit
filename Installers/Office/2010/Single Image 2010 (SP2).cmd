@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\..\..\.bin\Scripts\Launch.cmd" Office "%~dp0\..\..\..\.bin\Scripts" "2010\Single Image 2010 (SP2)"
