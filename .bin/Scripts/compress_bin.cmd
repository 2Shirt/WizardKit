@echo off

setlocal enabledelayedexpansion
pushd "%~dp0"

rem Prep
mkdir _out\_Drivers
set "out=%cd%\_out"

rem _Drivers
pushd _Drivers
for %%f in (*) do (
    set "file=%%f"
    "%programfiles%\7-Zip\7z.exe" a -t7z -mx=9 -myx=9 -ms=on -mhe -pAbracadabra "%out%\_Drivers\!file:~0,-4!.7z" "%%f"
)
popd

rem Rest
for /d %%d in (*) do (
    if not "%%d" == "_out" (
        pushd "%%d"
        "%programfiles%\7-Zip\7z.exe" a -t7z -mx=9 -myx=9 -ms=on -mhe -pAbracadabra "%out%\%%d.7z" *
        popd
    )
)

popd
endlocal