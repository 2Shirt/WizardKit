# WK-Check Disk

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK Check Disk Tool"

## Schedule CHKDSK ##
write-host "$systemdrive (System Drive)"
start -wait "chkdsk" -argumentlist @("/f", "$systemdrive") -nonewwindow

## Done ##
popd
pause "Press Enter to reboot..."
restart-computer
