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

:ModifySettings
reg add HKCU\Software\Sysinternals\AutoRuns /v checkvirustotal /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v EulaAccepted /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v shownomicrosoft /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v shownowindows /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v showonlyvirustotal /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v submitvirustotal /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns /v verifysignatures /t REG_DWORD /d 0 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns\SigCheck /v EulaAccepted /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns\Streams /v EulaAccepted /t REG_DWORD /d 1 /f >nul
reg add HKCU\Software\Sysinternals\AutoRuns\VirusTotal /v VirusTotalTermsAccepted /t REG_DWORD /d 1 /f >nul

:Launch
call "%bin%\Scripts\Launch.cmd" Program "%bin%\SysinternalsSuite" "Autoruns.exe" "-e"
goto Exit

:ErrorNoBin
popd
color 4e
echo ".bin" folder not found, aborting script.
echo.
echo Press any key to exit...
pause>nul
color
goto Exit

:Exit
