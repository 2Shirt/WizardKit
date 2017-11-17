@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

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
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\WinDirStat" "windirstat.exe" "" /admin /max