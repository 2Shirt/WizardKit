@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" chocolatey "%userprofile%" "classic-shell -installArgs ADDLOCAL=ClassicStartMenu"
echo "Please wait until Classic Shell is installed before continuing."
echo.
ping 127.0.0.1 -n 3 >nul 2>&1
echo "Press any key to continue..."
pause>nul
call "%~dp0\..\.bin\Scripts\Launch.cmd" chocolatey "%userprofile%" "7zip.install googlechrome firefox mpv.install vlc adobeair adobereader adobereader-update jre8 silverlight dotnet3.5 dotnet4.5.1" /wait