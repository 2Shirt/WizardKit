# WK-Enter SafeMode

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK SafeMode Tool"

# Ask user
if (!(ask "Enable booting to SafeMode (with Networking)?")) {
    # Abort
    # TODO: test this
    popd
    exit 1
}

## Configure OS ##
# Edit BCD
start -wait "bcdedit" -argumentlist @("/set", "{default}", "safeboot", "network") -nonewwindow

# Enable MSI access under safemode
# TODO

## Done ##
popd
pause "Press Enter to reboot..."
restart-computer
