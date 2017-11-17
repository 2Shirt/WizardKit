@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" chocolatey "%userprofile%" "7zip.install googlechrome firefox mpv.install vlc microsoftsecurityessentials adobeair adobereader adobereader-update jre8 silverlight dotnet3.5 dotnet4.5.1"