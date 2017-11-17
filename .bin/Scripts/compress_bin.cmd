@echo off

setlocal
pushd "%~dp0"

for /d %%d in (*) do (
    pushd "%%d"
    "%programfiles%\7-Zip\7z.exe" a -t7z -mx=9 -myx=9 -ms=on -mhe -pAbracadabra "..\%%d.7z" *
    popd
)

popd
endlocal