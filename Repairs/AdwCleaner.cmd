@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Copy
cd /d "%~dp0\..\.bin"
set "prog=AdwCleaner.exe"
mkdir "tmp" >nul 2>&1
copy /y "%prog%" "tmp\%prog%"

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "%prog%" ""