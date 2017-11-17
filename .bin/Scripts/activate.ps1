# WK-Activate-w-BIOS-Key
#
## Finds the BIOS key using ProduKey and attempts to activate Windows with it
## NOTE: This script doesn't check if the key is accepted before activation.

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK Activation Tool"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\Activation.log"
$bin = (Get-Item $wd).Parent.FullName
$found_key = $false

# OS Check
. .\os_check.ps1

## Extract ProduKey
md "$bin\ProduKey" 2>&1 | out-null
start -wait "$bin\7-Zip\7z.exe" -argumentlist @("x", "$bin\ProduKey.7z", "-o$bin\ProduKey", "-aos", "-pGerbil14") -workingdirectory "$bin\7-Zip" -nonewwindow -redirectstandardoutput out-null
sleep -s 1

## Get Key ##
ri "$bin\ProduKey\*.cfg"
if ($arch -eq 64) {
    $prog = "$bin\ProduKey\ProduKey64.exe"
} else {
    $prog = "$bin\ProduKey\ProduKey.exe"
}
$produkey_args = @(
    "/nosavereg",
    "/scomma", "$logpath\keys.csv",
    "/WindowsKeys", "1",
    "/OfficeKeys", "0",
    "/IEKeys", "0",
    "/SQLKeys", "0",
    "/ExchangeKeys", "0"
)
start -wait $prog -argumentlist $produkey_args -workingdirectory "$bin\ProduKey"
$keys = import-csv -header ("Name", "ID", "Key") "$logpath\keys.csv"

## Find BIOS Key and activate Windows with it
foreach ($k in $keys) {
    $name = $k.Name
    $key = $k.Key
    if ($name -match 'BIOS' -and $key -match '^(\w{5}-\w{5}-\w{5}-\w{5}-\w{5})$') {
        # NOTE: Assuming first match is correct and skip everything afterwards
        $found = $true
        wk-write "$name key found: $key" "$log"
        if (ask "  Activate Windows using this key?" "$log") {
            start -wait "cscript.exe" -argumentlist @("slmgr.vbs", "/ipk", "$key", "//nologo") -nonewwindow -workingdirectory "$windir\System32"
            start -wait "cscript.exe" -argumentlist @("slmgr.vbs", "/ato", "//nologo") -nonewwindow -workingdirectory "$windir\System32"
            start -wait "cscript.exe" -argumentlist @("slmgr.vbs", "/xpr", "//nologo") -nonewwindow -workingdirectory "$windir\System32"
        }
        break
    }
}

## Print error if necessary
if (! $found) {
    wk-error "BIOS Key not found." "$log"
}

## Done ##
popd
pause "Press Enter to exit..."
