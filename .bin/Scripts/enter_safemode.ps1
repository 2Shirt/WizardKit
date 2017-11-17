# Wizard Kit: Enter SafeMode by setting it as {default}

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: SafeMode Tool"

# Ask user
if (!(ask "Enable booting to SafeMode (with Networking)?")) {
    popd
    exit 1
}

## Configure OS ##
# Edit BCD
start -wait "bcdedit" -argumentlist @("/set", "{default}", "safeboot", "network") -nonewwindow

# Enable MSI access under safemode
New-Item "HKLM:\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer" 2>&1 | out-null
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer" -Name "(Default)" -Value "Service" -Type "String" -Force | out-null

## Done ##
popd
pause "Press Enter to reboot..."
restart-computer
