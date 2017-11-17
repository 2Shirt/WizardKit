@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Extract
if not exist "%~dp0\..\.bin\ProduKey" (
    mkdir "%~dp0\..\.bin\ProduKey" >nul 2>&1
    call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "%~dp0\..\.bin\7-Zip\7z.exe" "x ProduKey.7z -oProduKey -aos -pAbracadabra" /wait
    ping -n 1 127.0.0.1>nul
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Console "%~dp0\..\.bin\Scripts" "transferred_keys.cmd" /admin