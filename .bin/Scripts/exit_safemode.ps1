# WK-Exit SafeMode

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK SafeMode Tool"

# Ask user
if (!(ask "Disable booting to SafeMode?")) {
    popd
    exit 1
}

## Configure OS ##
# Edit BCD
start -wait "bcdedit" -argumentlist @("/deletevalue", "{current}", "safeboot") -nonewwindow
start -wait "bcdedit" -argumentlist @("/deletevalue", "{default}", "safeboot") -nonewwindow

# Disable MSI access under safemode
Remove-Item -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer" -Recurse 2>&1 | out-null

## Done ##
popd
pause "Press Enter to reboot..."
restart-computer
