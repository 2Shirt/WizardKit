@echo off

rem Set date variable and create WK\Info\%date%

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:GetDate
:: Credit to SS64.com Code taken from http://ss64.com/nt/syntax-getdate.html
:: Use WMIC to retrieve date and time in ISO 8601 format.
FOR /F "skip=1 tokens=1-6" %%G IN ('WMIC Path Win32_LocalTime Get Day^,Hour^,Minute^,Month^,Second^,Year /Format:table') DO (
IF "%%~L"=="" goto s_done
    Set _yyyy=%%L
    Set _mm=00%%J
    Set _dd=00%%G
    Set _hour=00%%H
    SET _minute=00%%I
)
:s_done
:: Pad digits with leading zeros
Set _mm=%_mm:~-2%
Set _dd=%_dd:~-2%
Set _hour=%_hour:~-2%
Set _minute=%_minute:~-2%
Set iso_date=%_yyyy%-%_mm%-%_dd%

:CreateInfoDir
set "log_dir=%systemdrive%\WK\Info\%iso_date%"
mkdir "%log_dir%">nul 2>&1

:Done
goto Exit

:Exit