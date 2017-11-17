@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:RestoreDefaults
del "xmplay.library"
del "xmplay.library~"
del "xmplay.pls"
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\XMPlay" "%~dp0\..\.bin\7-Zip\7z.exe" "e defaults.7z -aoa"

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\XMPlay" "xmplay.exe" "music.7z"