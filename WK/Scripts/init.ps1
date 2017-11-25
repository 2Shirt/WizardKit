# WK-Init
#
# Some common settings and functions

$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "green"
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
function pause {
    param([string]$message = "Press Enter to continue... ")
    write-host $message
    $x = read-host
}
