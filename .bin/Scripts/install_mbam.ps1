# WK Install and run MBAM 

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK / Chocolatey Installer"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\Chocolatey.log"

## Install/Upgrade Chocolatey ##
$choco = "$programdata\chocolatey\choco.exe"
if (test-path "$choco") {
    start "choco" -argumentlist @("upgrade", "chocolatey", "-y") -nonewwindow -wait
} else {
    .\install_chocolatey.ps1
}

## Network Check ##
wk-write "* Testing Internet Connection" "$log"
if (!(test-connection "google.com" -count 2 -quiet)) {
    wk-warn "System appears offline. Please connect to the internet." "$log"
    pause
    if (!(test-connection "google.com" -count 2 -quiet)) {
        wk-error "System still appears offline; aborting script." "$log"
        exit 1
    }
}

## Install ##
start -wait "$programdata\chocolatey\choco.exe" -argumentlist @("upgrade", "-y", "malwarebytes") -nonewwindow

## Launch MBAM ##
if (test-path "$programfiles\Malwarebytes Anti-Malware\mbam.exe") {
    start "$programfiles\Malwarebytes Anti-Malware\mbam.exe"
} elseif (test-path "$programfiles86\Malwarebytes Anti-Malware\mbam.exe") {
    start "$programfiles86\Malwarebytes Anti-Malware\mbam.exe"
}

## Done ##
popd
pause "Press Enter to exit..."
exit