@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:FindBin
set bin=
pushd "%~dp0"
:FindBinInner
if exist ".bin" (
    set "bin=%cd%\.bin"
    goto FindBinDone
)
if "%~d0\" == "%cd%" (
    goto FindBinDone
) else (
    cd ..
)
goto FindBinInner
:FindBinDone
popd
if not defined bin goto ErrorNoBin

:ModifySettings
reg add HKCU\Software\Seifert\WinDirStat\options /v followJunctionPoints /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v followMountPoints /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v humanFormat /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v language /t REG_DWORD /d 409 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v listFullRowSelection /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v listStripes /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v pacmanAnimation /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v showTimeSpent /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v treelistGrid /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v treemapGrid /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\options /v useWdsLocale /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Seifert\WinDirStat\persistence /v showTreemap /t REG_DWORD /d 0 /f >nul

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\WinDirStat" "windirstat.exe" "" /admin /max
goto Exit

:ErrorNoBin
color 4e
echo ".bin" folder not found, aborting script.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:Exit
