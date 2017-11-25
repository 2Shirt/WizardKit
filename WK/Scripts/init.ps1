# WK-Init
#
# Some common settings and functions

$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "cyan"
$systemdrive = (gci env:systemdrive).value
$WKPath = "$systemdrive\WK"
$date = get-date -uformat "%Y-%m-%d"

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
function pause {
    param([string]$message = "Press Enter to continue... ", [bool]$warning = $False)
    if ($warning) {
        write-host ($message) -foreground "yellow"
    } else {
        write-host ($message)
    }
    $x = read-host
}
