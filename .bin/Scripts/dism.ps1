# WK-DISM wrapper

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK DISM wrapper"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\DISM.log"
$bin = (Get-Item $wd).Parent.FullName

# OS Check
. .\os_check.ps1
if ($win_version -le 7 -Or $win_version -imatch 'Vista') {
    wk-error "This tool is not intended for $os_name."
} else {
    # Get mode
    $modes = @(
        @{Name="Check Health";      Command="/CheckHealth"}
        @{Name="Restore Health";    Command="/Online /Cleanup-Image /RestoreHealth"}
    )
    $selection = (menu-select "WK DISM Wrapper" "Please select action to perform" $modes)
    $command = "DISM {0}" -f $modes[$selection - 1].Command
    sleep -s 1
    start "DISM" -argumentlist @("/Online", "/Cleanup-Image", "$command", "/LogPath:$log") -NoNewWindow -Wait -RunAs
}

# Done
pause "Press any key to exit..."