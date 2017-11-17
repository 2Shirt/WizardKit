@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Extract
mkdir "%~dp0\..\.bin\mailpv" >nul 2>&1
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "%~dp0\..\.bin\7-Zip\7z.exe" "x mailpv.7z -omailpv -aos -Abracadabra" /wait
ping -n 1 127.0.0.1>nul

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\mailpv" "mailpv.exe" "" /admin