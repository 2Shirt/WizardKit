@echo off

:Flags
set fix=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
    if /i "%%f" == "/f" (set fix=/f)
)

:Init
title Wizard Kit: CheckDisk
color 1b

:ScheduleCheck
chkdsk %fix% %systemdrive%
if defined fix (
    echo Press any key to reboot... 
    pause>nul
    shutdown -r -t 10
) else (
    echo Press any ket to exit...
    pause>nul
)