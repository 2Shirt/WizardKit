@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Install
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "MBAM SAS.exe" "" /wait

:LaunchMBAM
if exist "%programfiles%\Malwarebytes Anti-Malware\mbam.exe" (call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%programfiles%\Malwarebytes Anti-Malware" "mbam.exe" "")
if exist "%programfiles(x86)%\Malwarebytes Anti-Malware\mbam.exe" (call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%programfiles(x86)%\Malwarebytes Anti-Malware" "mbam.exe" "")

:LaunchSAS
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%programfiles%\SUPERAntiSpyware" "SUPERAntiSpyware.exe" ""