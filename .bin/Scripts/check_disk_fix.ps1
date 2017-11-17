# WK-Check Disk

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK Check Disk Tool"

# OS Check
. .\os_check.ps1

## Run Scan (fix) ##
write-host "$systemdrive (System Drive)"
if ($win_version -match '^(8|10)$') {
    if (ask("Run Spot-fix and security cleanup?")) {
        start -wait "chkdsk" -argumentlist @("$systemdrive", "/sdcleanup", "/spotfix") -nonewwindow
    } else if (ask("Run full offline scan?")) {
        start -wait "chkdsk" -argumentlist @("$systemdrive", "/offlinescanandfix") -nonewwindow
    }
} else {
    start -wait "chkdsk" -argumentlist @("$systemdrive", "/F") -nonewwindow
}

## Done ##
popd
pause "Press Enter to reboot..."
restart-computer
