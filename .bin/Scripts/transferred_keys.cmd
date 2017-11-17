:: Wizard Kit: Scan all transferred software hive for product keys

@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:FindBin
set bin= & pushd "%~dp0"
:FindBinInner
if exist ".bin" goto FindBinDone
if "%~d0\" == "%cd%" goto ErrorNoBin
cd .. & goto FindBinInner
:FindBinDone
set "bin=%cd%\.bin" & popd

:Init
setlocal EnableDelayedExpansion
color 1b
title Wizard Kit: Key Finder
rem Create %client_dir%\Info\YYYY-MM-DD and set path as %log_dir%
call "%bin%\Scripts\init_client_dir.cmd" /Info
set "transfer_dir=%client_dir%\Transfer"

:ClearConfigs
if not exist "%bin%\tmp" goto Extract
pushd "%bin%\tmp"
if exist "ProduKey.cfg" del "ProduKey.cfg"
if exist "ProduKey64.cfg" del "ProduKey64.cfg"
popd

:Extract
mkdir "%bin%\tmp" >nul 2>&1
"%bin%\7-Zip\7za.exe" e "%bin%\ProduKey.7z" -o"%bin%\tmp" -aoa -pAbracadabra -bsp0 -bso0
ping -n 2 127.0.0.1>nul
set "prog=%bin%\tmp\ProduKey.exe"
if /i "!PROCESSOR_ARCHITECTURE!" == "AMD64" (
    if exist "!prog:.=64.!" set "prog=!prog:.=64.!"
)

:FindHives
cls
echo Scanning for transferred software hive(s)...
call :ScanHive "%transfer_dir%\Software"
call :ScanHive "%transfer_dir%\config\Software"
call :ScanHive "%transfer_dir%\config\RegBack\Software"
call :ScanHive "%transfer_dir%\Windows\System32\config\Software"
call :ScanHive "%transfer_dir%\Windows\System32\config\RegBack\Software"
call :ScanHive "%transfer_dir%\Windows.old\Software"
call :ScanHive "%transfer_dir%\Windows.old\config\Software"
call :ScanHive "%transfer_dir%\Windows.old\config\RegBack\Software"
call :ScanHive "%transfer_dir%\Windows.old\Windows\System32\config\Software"
call :ScanHive "%transfer_dir%\Windows.old\Windows\System32\config\RegBack\Software"
call :ScanHive "%transfer_dir%\Win.old\Software"
call :ScanHive "%transfer_dir%\Win.old\config\Software"
call :ScanHive "%transfer_dir%\Win.old\config\RegBack\Software"
call :ScanHive "%transfer_dir%\Win.old\Windows\System32\config\Software"
call :ScanHive "%transfer_dir%\Win.old\Windows\System32\config\RegBack\Software"

:ShowResults
if not exist "%log_dir%\transferred_keys.txt" (goto NoResults)
call "%bin%\Scripts\Launch.cmd" Program "%bin%\Notepad2" "Notepad2-Mod.exe" "%log_dir%\transferred_keys.txt"
goto Done

:ScanHive
if exist "%~1" (
    echo.   %~1
    echo ==== %~1 ====>> "%log_dir%\transferred_keys.txt"
    "%prog%" /IEKeys 0 /WindowsKeys 1 /OfficeKeys 1 /ExtractEdition 1 /nosavereg /regfile "%~1" /stext "" >> %log_dir%\transferred_keys.txt
)
goto :EOF

:NoResults
echo.
echo No keys found.
goto Error

:ErrorNoBin
popd
echo ".bin" folder not found, aborting script.
echo.
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
popd
color
endlocal

:EOF
