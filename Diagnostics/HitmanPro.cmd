@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as %log_dir%
call "%~dp0\..\.bin\Scripts\wk_info.cmd"

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\HitmanPro" "HitmanPro.exe" "/scan /noinstall /noupload /log=%log_dir%\hitman.xml" /admin