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
$sz = "$bin\7-Zip\7za.exe"
$produkey = "$bin\tmp\ProduKey.exe"

# OS Check
. .\os_check.ps1
if ($arch -eq 64) {
    $sz = "$bin\7-Zip\7za64.exe"
    $produkey = "$bin\tmp\ProduKey64.exe"
}

## Extract ProduKey
md "$bin\tmp" 2>&1 | out-null
start -wait $sz -argumentlist @("e", "$bin\ProduKey.7z", "-otmp", "-aoa", "-pAbracadabra", "-bsp0", "-bso0") -workingdirectory "$bin" -nonewwindow
rm "$bin\tmp\ProduKey*.cfg"
sleep -s 1

## Get Key ##
$produkey_args = @(
    "/nosavereg",
    "/scomma", "$logpath\keys.csv",
    "/WindowsKeys", "1",
    "/OfficeKeys", "0",
    "/IEKeys", "0",
    "/SQLKeys", "0",
    "/ExchangeKeys", "0"
)
start -wait $produkey -argumentlist $produkey_args -workingdirectory "$bin\tmp"
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
