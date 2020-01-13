:: Wizard Kit: Create client_dir folder(s)

@echo off
if defined DEBUG (@echo on)

:SafetyCheck
if not defined bin (goto Abort)

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

:SetVars
set "SETTINGS=%bin%\Scripts\settings\main.py"
for /f "tokens=* usebackq" %%f in (`findstr KIT_NAME_SHORT "%SETTINGS%"`) do (
  set "_v=%%f"
  set "_v=!_v:*'=!"
  set "KIT_NAME_SHORT=!_v:~0,-1!"
)
set "client_dir=%systemdrive%\%KIT_NAME_SHORT%"
set "log_dir=%client_dir%\Logs\%iso_date%"

:Flags
set _backups=
set _info=
set _office=
set _quarantine=
set _quickbooks=
set _transfer=
for %%f in (%*) do (
  if /i "%%f" == "/DEBUG" (@echo on)
  if /i "%%f" == "/Backups" set _backups=True
  if /i "%%f" == "/Logs" set _logs=True
  if /i "%%f" == "/Office" set _office=True
  if /i "%%f" == "/Quarantine" set _quarantine=True
  if /i "%%f" == "/QuickBooks" set _quickbooks=True
  if /i "%%f" == "/Transfer" set _transfer=True
)

:CreateDirs
if defined _backups mkdir "%client_dir%\Backups">nul 2>&1
if defined _logs (
  mkdir "%log_dir%\%KIT_NAME_FULL%">nul 2>&1
  mkdir "%log_dir%\Tools">nul 2>&1)
if defined _office mkdir "%client_dir%\Office">nul 2>&1
if defined _quarantine mkdir "%client_dir%\Quarantine">nul 2>&1
if defined _quickbooks mkdir "%client_dir%\QuickBooks">nul 2>&1
if defined _transfer mkdir "%client_dir%\Transfer_%iso_date%">nul 2>&1
goto Done

:Abort
color 4e
echo Aborted.
echo.
echo Press any key to exit...
pause>nul
color
rem Set errorlevel to 1 by calling color incorrectly
color 00
goto Exit

:Done
goto Exit

:Exit
