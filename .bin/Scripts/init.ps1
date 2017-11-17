# WK-Init
#
# Some common settings and functions

$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "green"
$appdata = (gci env:appdata).value
$localappdata = (gci env:localappdata).value
$username = (gci env:username).value
$userprofile = (gci env:userprofile).value
$systemdrive = (gci env:systemdrive).value
$windir = (gci env:windir).value
$programdata = (gci env:programdata).value
$programfiles = (gci env:programfiles).value
$programfiles86 = $programfiles
if (test-path env:"programfiles(x86)") {
    $programfiles86 = (gci env:"programfiles(x86)").value
}
$WKPath = "$systemdrive\WK"
$date = get-date -uformat "%Y-%m-%d"
$date_time = get-date -uformat "%Y-%m-%d_%H%M"
$logpath = "$WKPath\Info\$date"

function ask {
    param([string]$text = "Kotaero", [string]$log = "WK.log")
    $answered = $false
    $text += " [Y/N]"
    while (!$answered) {
        $answer = read-host $text
        if ($answer -imatch '^(y|yes)$') {
            $answer = $true
            $answered = $true
        } elseif ($answer -imatch '^(n|no)$') {
            $answer = $false
            $answered = $true
        }
    }
    $text += ": $answer"
    out-file -filepath $log -inputobject $text -append
    return $answer
}
function wk-error {
    param([string]$text = "ERROR", [string]$log = "WK.log")
    write-host ($text) -foreground "red"
    out-file -filepath $log -inputobject $text -append
}
function wk-warn {
    param([string]$text = "WARNING", [string]$log = "WK.log")
    write-host ($text) -foreground "yellow"
    out-file -filepath $log -inputobject $text -append
}
function wk-write {
    param([string]$text = "<TODO>", [string]$log = "WK.log")
    write-host ($text)
    out-file -filepath $log -inputobject $text -append
}
function menu-select {
    ## $MainItems should be an "AoH" object (with at least the key "Name" for each item)
    ## NOTE: if the CRLF=$true; then a spacer is added before that entry.
    ## Example:
    ## $MainItems = @(
    ##    @{Name="Windows 10 Home"; ImageFile="Win10"; ImageName="Windows 10 Home"}
    ##    @{Name="Windows 10 Pro";  ImageFile="Win10"; ImageName="Windows 10 Pro"}
    ##)
    
    ## $ActionItems should be an "AoH" object (with at least the keys "Name" and "Letter" for each item)
    ## NOTE: if the CRLF=$true; then a spacer is added before that entry.
    ## Example:
    ## $ActionItems = @(
    ##    @{Name="Reboot";   Letter="R"}
    ##    @{Name="Shutdown"; Letter="S"}
    ##)
    
    param(
        [string]$Title = "## Untitled Menu ##",
        [string]$Prompt = "Please make a selection",
        $MainItems = @(),
        $ActionItems = @()
    )
    
    # Bail early if no items given
    if ($MainItems.length -eq 0 -and $ActionItems.length -eq 0) {
        throw "MenuError: No items given."
    }
    
    # Build menu
    $menu_splash = "{0}`r`n`r`n" -f $title
    $valid_answers = @()
    
    # Add main items to splash
    if ($MainItems.length -gt 0) {
        for ($i=0; $i -lt $MainItems.length; $i++) {
            if ($MainItems[$i].CRLF) {
                # Add spacer
                $menu_splash += "`r`n"
            }
            $valid_answers += ($i + 1)
            $menu_splash += "{0,2:N0}: {1}`r`n" -f ($i + 1), $MainItems[$i].Name
        }
        $menu_splash += "`r`n"
        $menu_splash += "`r`n"
    }
    
    # Add action items to splash
    if ($ActionItems.length -gt 0) {
        foreach ($_item in $ActionItems) {
            if ($_item.CRLF) {
                # Add spacer
                $menu_splash += "`r`n"
            }
            $menu_splash += "{0}: {1}`r`n" -f $_item.Letter.ToUpper(), $_item.Name
            $valid_answers += $_item.Letter.ToLower(), $_item.Letter.ToUpper()
        }
        $menu_splash += "`r`n"
    }
    
    # Add prompt to splash
    $menu_splash += "{0}`r`n" -f $prompt
    
    # Select
    do {
        clear
        $answer = read-host -prompt $menu_splash
    } until ($valid_answers -contains $answer)
    
    return $answer.ToUpper()
}
function pause {
    param([string]$message = "Press Enter to continue... ")
    write-host $message
    $x = read-host
}
