@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:OpenFolder
cd /d %~dp0
start "" "explorer.exe" "%cd%\..\.bin\SysinternalsSuite"