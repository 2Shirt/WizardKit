@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as %log_dir%
call "%~dp0\..\.bin\Scripts\wk_info.cmd"

:LaunchERUNT
rem Backup registry before running WinAIO
echo Backing up registry...
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\erunt" "ERUNT.EXE" "%log_dir%\Registry sysreg curuser otherusers" /admin /wait

:LaunchWinAIO
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\Complete Internet Repair" "ComIntRep.exe" ""