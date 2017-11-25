# WK-Init
#
# Some common settings and functions

$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "cyan"
#$appdata = (gci env:appdata).value
#$localappdata = (gci env:localappdata).value
#$username = (gci env:username).value
#$userprofile = (gci env:userprofile).value
$systemdrive = (gci env:systemdrive).value
$windir = (gci env:windir).value
#$programfiles = (gci env:programfiles).value
#$programfiles86 = $programfiles
#if (test-path env:"programfiles(x86)") {
#    $programfiles86 = (gci env:"programfiles(x86)").value
#}
$WKPath = "$systemdrive\WK"
$date = get-date -uformat "%Y-%m-%d"
#$logpath = "$WKPath\Info\$date"

# Check if booted via UEFI
$UEFI = $false
if ((Get-ItemProperty -path "HKLM:\System\CurrentControlSet\Control").PEFirmwareType -eq 2) {
    $UEFI = $true
}

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
function human-size {
    param($bytes, [int]$decimals = 2)
    if ($bytes -gt 1Tb) {
        $size = "{0:N$decimals} Tb" -f ($bytes / 1Tb)
    } elseif ($bytes -gt 1Gb) {
        $size = "{0:N$decimals} Gb" -f ($bytes / 1Gb)
    } elseif ($bytes -gt 1Mb) {
        $size = "{0:N$decimals} Mb" -f ($bytes / 1Mb)
    } elseif ($bytes -gt 1Kb) {
        $size = "{0:N$decimals} Kb" -f ($bytes / 1Kb)
    } else {
        $size = "{0:N$decimals}  b" -f $bytes
    }
    return $size
}
function menu-select {
    ## $MainEntries should be an "AoH" object (with at least the key "Name" for each item)
    ## NOTE: if the CRLF=$true; then a spacer is added before that entry.
    ## Example:
    ## $MainEntries = @(
    ##    @{Name="Windows 10 Home"; ImageFile="Win10"; ImageName="Windows 10 Home"}
    ##    @{Name="Windows 10 Pro";  ImageFile="Win10"; ImageName="Windows 10 Pro"}
    ##)
    
    ## $ActionEntries should be an "AoH" object (with at least the keys "Name" and "Letter" for each item)
    ## NOTE: if the CRLF=$true; then a spacer is added before that entry.
    ## Example:
    ## $ActionEntries = @(
    ##    @{Name="Reboot";   Letter="R"}
    ##    @{Name="Shutdown"; Letter="S"}
    ##)
    
    param(
        [string]$Title = "## Untitled Menu ##",
        $MainEntries = @(),
        $ActionEntries = @(),
        [string]$Prompt = "Please make a selection",
        [bool]$SecretExit = $false
    )
    
    # Bail early if no items given
    if ($MainEntries.length -eq 0 -and $ActionEntries.length -eq 0) {
        throw "MenuError: No items given."
    }
    
    # Build menu
    $menu_splash = "{0}`r`n`r`n" -f $title
    $valid_answers = @()
    if ($SecretExit) {
        $valid_answers += "Q"
    }
    
    # Add main items to splash
    if ($MainEntries.length -gt 0) {
        for ($i=0; $i -lt $MainEntries.length; $i++) {
            if ($MainEntries[$i].CRLF) {
                # Add spacer
                $menu_splash += "`r`n"
            }
            $valid_answers += ($i + 1)
            $menu_splash += "{0,2:N0}: {1}`r`n" -f ($i + 1), $MainEntries[$i].Name
        }
        $menu_splash += "`r`n"
    }
    
    # Add action items to splash
    if ($ActionEntries.length -gt 0) {
        foreach ($_item in $ActionEntries) {
            if ($_item.CRLF) {
                # Add spacer
                $menu_splash += "`r`n"
            }
            $menu_splash += " {0}: {1}`r`n" -f $_item.Letter.ToUpper(), $_item.Name
            $valid_answers += $_item.Letter.ToLower(), $_item.Letter.ToUpper()
        }
        $menu_splash += "`r`n"
    }
    
    # Add prompt to splash
    $menu_splash += "{0}`r`n" -f $prompt
    
    # Select Windows version
    do {
        clear
        $answer = read-host -prompt $menu_splash
    } until ($valid_answers -contains $answer)
    
    return $answer.ToUpper()
}
function pause {
    param([string]$message = "Press Enter to continue... ", [bool]$warning = $False)
    if ($warning) {
        write-host ($message) -foreground "yellow"
    } else {
        write-host ($message)
    }
    $x = read-host
}
