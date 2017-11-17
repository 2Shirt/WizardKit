@echo off

rem This script assumes it is running as admin, as such it is not meant to be run directly.

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Init
setlocal EnableDelayedExpansion
color 1b
title WK Key Finder

:ClearConfigs
if exist "ProduKey\ProduKey.cfg" del "ProduKey\ProduKey.cfg"
if exist "ProduKey\ProduKey64.cfg" del "ProduKey\ProduKey64.cfg"

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as !log_dir!
call "wk_info.cmd"

:FindHives
echo Scanning for transferred software hive(s)...
set "found_hive="
rem Transferred (Main)
set "sw_hive=%systemdrive%\WK\Transfer\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)
set "sw_hive=%systemdrive%\WK\Transfer\Windows\System32\config\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)
set "sw_hive=%systemdrive%\WK\Transfer\Windows\System32\config\RegBack\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)

rem Transferred (Win.old)
set "sw_hive=%systemdrive%\WK\Transfer\Win.old\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)
set "sw_hive=%systemdrive%\WK\Transfer\Windows.old\Windows\System32\config\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)
set "sw_hive=%systemdrive%\WK\Transfer\Windows.old\Windows\System32\config\RegBack\Software"
if exist "!sw_hive!" (
    set "found_hive=true"
    echo.   !sw_hive!
    echo ==== !sw_hive! ====>> "!log_dir!\transferred_keys.txt"
    call "Launch.cmd" Program "!cd!\..\ProduKey" "ProduKey.exe" "/IEKeys 0 /ExtractEdition 1 /nosavereg /regfile !sw_hive! /stext !log_dir!\transferred_keys.tmp" /wait /admin
    type "!log_dir!\transferred_keys.tmp">> "!log_dir!\transferred_keys.txt"
    del "!log_dir!\transferred_keys.tmp"
)

:ShowResults
if not defined found_hive (goto NoResults)
call "Launch.cmd" Program "!cd!\..\Notepad2" "Notepad2-Mod.exe" "!log_dir!\transferred_keys.txt"
goto Done

:NoResults
echo.
echo No keys found.
goto Error

:Error
color 4e
echo.
echo Press any key to exit...
pause>nul
goto Exit

:Done
goto Exit

:Exit
rem pause
popd
color
endlocal