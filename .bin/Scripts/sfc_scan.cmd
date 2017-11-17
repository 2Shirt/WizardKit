@echo off

:Flags
set fix=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
    if /i "%%f" == "/f" (set fix=/f)
)

:Init
title WK System File Checker
color 1b

:ScheduleCheck
sfc /scannow

:Done
echo Press any key to exit...
pause>nul