:: Wizard Kit: Create client_dir folder(s)

@echo off
if defined DEBUG (@echo on)

:Flags
set _backups=
set _info=
set _office=
set _quarantine=
set _transfer=
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
    if /i "%%f" == "/Backups" set _backups=True
    if /i "%%f" == "/Info" set _info=True
    if /i "%%f" == "/Office" set _office=True
    if /i "%%f" == "/Quarantine" set _quarantine=True
    if /i "%%f" == "/Transfer" set _transfer=True
)

:GetDate
:: Credit to SS64.com Code taken from http://ss64.com/nt/syntax-getdate.html
:: Use WMIC to retrieve date and time in ISO 8601 format.
for /f "skip=1 tokens=1-6" %%G in ('WMIC Path Win32_LocalTime Get Day^,Hour^,Minute^,Month^,Second^,Year /Format:table') do (
    if "%%~L"=="" goto s_done
    set _yyyy=%%L
    set _mm=00%%J
    set _dd=00%%G
    set _hour=00%%H
    set _minute=00%%I
)
:s_done
:: Pad digits with leading zeros
set _mm=%_mm:~-2%
set _dd=%_dd:~-2%
set _hour=%_hour:~-2%
set _minute=%_minute:~-2%
set iso_date=%_yyyy%-%_mm%-%_dd%

:SetVariables
set "client_dir=%systemdrive%\WK"
set "log_dir=%client_dir%\Info\%iso_date%"

:CreateDirs
if defined _backups mkdir "%client_dir%\Backups">nul 2>&1
if defined _info mkdir "%client_dir%\Info">nul 2>&1
if defined _office mkdir "%client_dir%\Office">nul 2>&1
if defined _quarantine mkdir "%client_dir%\Quarantine">nul 2>&1
if defined _transfer mkdir "%client_dir%\Transfer">nul 2>&1

:Done
goto Exit

:Exit