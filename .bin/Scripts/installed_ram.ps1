# Wizard Kit: List installed RAM (and speed if possible)

param([string]$log)

cd $(Split-Path $MyInvocation.MyCommand.Path)
. .\init.ps1

$ram_speeds = @{
    "100" = "DDR-200 (PC-1600)";
    "133" = "DDR-266 (PC-2100)";
    "134" = "DDR-266 (PC-2100)";
    "166" = "DDR-333 (PC-2700)";
    "167" = "DDR-333 (PC-2700)";
    "200" = "[DDR|DDR2]-400 ([PC|PC2]-3200)";
    "266" = "DDR2-533 (PC2-4200)";
    "267" = "DDR2-533 (PC2-4200)";
    "333" = "DDR2-667 (PC2-5300)";
    "334" = "DDR2-667 (PC2-5300)";
    "400" = "[DDR2|DDR3]-800 ([PC2|PC3]-6400)";
    "533" = "[DDR2|DDR3]-1066 ([PC2|PC3]-8500)";
    "534" = "[DDR2|DDR3]-1066 ([PC2|PC3]-8500)";
    "666" = "DDR3-1333 (PC3-10600)";
    "667" = "DDR3-1333 (PC3-10600)";
    "800" = "[DDR3|DDR4]-1600 (PC3-12800 / PC4-1600)";
    "933" = "[DDR3|DDR4]-1866 (PC3-14900 / PC4-1866)";
    "934" = "[DDR3|DDR4]-1866 (PC3-14900 / PC4-1866)";
    "1066" = "[DDR3|DDR4]-2133 (PC3-17000 / PC4-2133)";
    "1067" = "[DDR3|DDR4]-2133 (PC3-17000 / PC4-2133)";
    "1200" = "DDR4-2400 (PC4-2400)";
}

$cs = Get-WmiObject -Class Win32_ComputerSystem
$mem = Get-WmiObject -Class Win32_PhysicalMemory
$total = 0
foreach ($dev in $mem) {
    $_size = $dev.Capacity/1gb
    $_loc = $dev.DeviceLocator
    $_type = $ram_speeds."$($dev.Speed)"
    WK-write $("  {0:N2} Gb ({1}) {2}" -f $_size,$_loc,$_type) "$log"
    $total += $dev.Capacity
}
WK-write "  -------" "$log"
WK-write $("  {0:N2} Gb Usable" -f $($cs.TotalPhysicalMemory/1gb)) "$log"
WK-write $("  {0:N2} Gb Installed" -f $($total/1gb)) "$log"
