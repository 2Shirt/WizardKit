# Wizard Kit: Check Disk

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Check Disk Tool"

# OS Check
. .\check_os.ps1

## Run Scan (read-only) ##
write-host "$systemdrive (System Drive)"
if ($win_version -match '^(8|10)$') {
    start -wait "chkdsk" -argumentlist @("$systemdrive", "/scan", "/perf") -nonewwindow
} else {
    start -wait "chkdsk" -argumentlist @("$systemdrive") -nonewwindow
}

## Done ##
popd
pause "Press Enter to exit..."
