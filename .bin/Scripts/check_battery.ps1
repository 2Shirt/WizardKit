# Wizard Kit: List battery health by checking the current max charge against the original value

param([string]$log = "Battery.log")
if ($log -match '^Battery.log$') {
    $log = "{0}\Battery.log" -f (gci env:temp).value
}

pushd $(Split-Path $MyInvocation.MyCommand.Path)
. .\init.ps1

try {
    $designed_full = (get-wmiobject -class "BatteryStaticData" -namespace "ROOT\WMI").DesignedCapacity 2>out-null
    $last_full = (get-wmiobject -class "BatteryFullChargedCapacity" -namespace "ROOT\WMI").FullChargedCapacity 2>out-null
    $last_percentage = ($last_full / $designed_full) * 100
    $message = "  Last full charge was {0:N0}% of designed capacity" -f $last_percentage

    if ($last_percentage -eq 100) {
        WK-warn "  Unable to determine battery health" "$log"
    } elseif ($last_percentage -ge 90) {
        WK-write $message "$log"
    } elseif ($last_percentage -ge 50) {
        WK-warn $message "$log"
    } else {
        WK-error $message "$log"
    }
} catch {
    WK-warn "  No battery detected" "$log"
}

## Done ##
popd
