@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
pushd "%~dp0\..\.bin\_Removal Tools"
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%windir%" "explorer.exe" "%cd%"
popd