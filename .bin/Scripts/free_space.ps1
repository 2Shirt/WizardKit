param([string]$log)

cd $(Split-Path $MyInvocation.MyCommand.Path)
. .\init.ps1

foreach ($d in [char]'C'..[char]'Z') {
    $letter = "$([char]$d):"
    if (-not $(test-path "$letter\")) {continue}
    $drive = $(fsutil volume diskfree $letter) -replace '^.*: ',''
    if ($lastexitcode -ne 0) {continue}
    $percent = ($drive[2] / $drive[1]) * 100
    foreach ($x in 0,1,2) {
        $tmp = [int64]$drive[$x]
        if ($tmp -ge 1tb) {
            $tmp /= 1tb
            $tmp = "{0:N2} Tb" -f $tmp
        } elseif ($tmp -ge 1gb) {
            $tmp /= 1gb
            $tmp = "{0:N2} Gb" -f $tmp
        } elseif ($tmp -ge 1mb) {
            $tmp /= 1mb
            $tmp = "{0:N2} Mb" -f $tmp
        } elseif ($tmp -ge 1kb) {
            $tmp /= 1kb
            $tmp = "{0:N2} Kb" -f $tmp
        } else {
            $tmp = "$tmp bytes"
        }
        $drive[$x] = $tmp
    }
    wk-write $("  {0}  {1:N0}% Free  ({2} / {3})" -f $letter, $percent, $drive[2], $drive[1]) $log
}
