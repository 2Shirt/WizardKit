# Wizard Kit: Final Checklist

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Checklist Tool"
$logpath = "$ClientPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\Checklist.log"
$bin = (Get-Item $wd).Parent.FullName
$diag_dest = "/srv/Diagnostics"
$diag_server = "10.0.0.10"
$diag_user = "WKdiag"
$sz = "$bin\7-Zip\7za.exe"
$produkey = "$bin\tmp\ProduKey.exe"

# OS Check
. .\check_os.ps1
if ($arch -eq 64) {
    $sz = "$bin\7-Zip\7za64.exe"
    $produkey = "$bin\tmp\ProduKey64.exe"
}

# Set Service Order
while ($service_order -notmatch '^\d+') {
    $service_order = read-host "Please enter the service order number"
    if ($service_order -notmatch '^\d+') {
        write-host "ERROR: Invalid SO`r`n" -foreground "red"
    }
}
clear
out-file -filepath "$logpath\TicketNumber" -inputobject $service_order -append
WK-write "Starting final checklist for Ticket #$service_order" "$log"
WK-write "" "$log"

## Cleanup ##
WK-write "Pre-Checklist Cleanup" "$log"

# Uninstall AdwCleaner
if (test-path "$systemdrive\AdwCleaner") {
	try {
		WK-write "* Uninstalling AdwCleaner" "$log"
		move-item "$systemdrive\AdwCleaner\*log" "$ClientPath\Info\"
		move-item "$systemdrive\AdwCleaner\*txt" "$ClientPath\Info\"
		if (test-path "$systemdrive\AdwCleaner\Quarantine") {
			move-item "$systemdrive\AdwCleaner\Quarantine" "$ClientPath\Quarantine\AdwCleaner"
		}
		remove-item "$systemdrive\AdwCleaner" -recurse
    } catch {
		WK-error "  Failed to uninstall AdwCleaner; please remove manually." "$log"
    }
}

# Uninstall Autoruns
if (test-path "HKCU:\Software\Sysinternals\AutoRuns") {
    WK-write "* Uninstalling Autoruns" "$log"
    Remove-Item -Path HKCU:\Software\Sysinternals\AutoRuns -Recurse 2>&1 | out-null
    if ((Get-ChildItem -Path HKCU:\Software\Sysinternals 2> out-null | Measure-Object).count -eq 0) {
        Remove-Item -Path HKCU:\Software\Sysinternals 2>&1 | out-null
    }
}

# Uninstall ESET
if (test-path "$programfiles86\ESET\ESET Online Scanner") {
    WK-write "* Uninstalling ESET" "$log"
    start -wait "$programfiles86\ESET\ESET Online Scanner\OnlineScannerUninstaller.exe" -argumentlist "/s"
    rm -path "$programfiles86\ESET\ESET Online Scanner" -recurse 2>&1 | out-null
    if ((gci -path "$programfiles86\ESET" 2> out-null | Measure-Object).count -eq 0) {
        rm -path "$programfiles86\ESET" 2>&1 | out-null
    }
}

# Move JRT logs & backups
if (test-path "$userprofile\Desktop\JRT*") {
    WK-write "* Cleaning up JRT leftovers" "$log"
    WK-warn "  TODO" "$log"
}

# Uninstall MBAM
if (test-path "$programfiles86\Malwarebytes") {
    WK-warn "Malwarebytes Anti-Malware installation found." "$log"
    if (ask "  Uninstall?" "$log") {
        WK-write "* Uninstalling Malwarebytes Anti-Malware" "$log"
        WK-warn "  TODO" "$log"
    }
}

# Move RKill logs & backups
if (test-path "$userprofile\Desktop\rkill*") {
    WK-write "* Cleaning up RKill leftovers" "$log"
    WK-warn "  TODO" "$log"
}

# Uninstall SUPERAntiSpyware
# It is always in programfiles (not x86) ??
$sas_force_remove = $false
if (test-path "$programfiles\SUPERAntiSpyware") {
    WK-warn "SUPERAntiSpyware installation found." "$log"
    if (ask "  Uninstall?" "$log") {
        if (test-path "$programfiles\SUPERAntiSpyware\Uninstall.exe") {
            WK-write "* Uninstalling SUPERAntiSpyware" "$log"
            start -wait "$programfiles\SUPERAntiSpyware\Uninstall.exe"
        } else {
            WK-error "The SUPERAntiSpyware removal tool will be used as the installation is damaged" "$log"
            $sas_force_remove = $true
        }
    }
}

## Summary ##
WK-write "" "$log"
WK-write "Starting SW Checklist" "$log"
WK-write "" "$log"

# Backup Registry
if (!(test-path "$logpath\Registry")) {
    WK-write "* Backing up registry" "$log"
    start -wait "$bin\Erunt\ERUNT.EXE" -argumentlist @("$logpath\Registry", "sysreg", "curuser", "otherusers", "/noprogresswindow") -workingdirectory "$bin\Erunt"
}

# AIDA64
if (!(test-path "$logpath\keys-aida64.txt")) {
    WK-write "* Running AIDA64 (Product Keys)" "$log"
    start -wait "$bin\AIDA64\aida64.exe" -argumentlist @("/R", "$logpath\keys-aida64.txt", "/CUSTOM", "$bin\AIDA64\licenses.rpf", "/TEXT", "/SILENT", "/SAFEST") -workingdirectory "$bin\AIDA64"
}

if (!(test-path "$logpath\program_list-aida64.txt")) {
    WK-write "* Running AIDA64 (SW listing)" "$log"
    start -wait "$bin\AIDA64\aida64.exe" -argumentlist @("/R", "$logpath\program_list-aida64.txt", "/CUSTOM", "$bin\AIDA64\installed_programs.rpf", "/TEXT", "/SILENT", "/SAFEST") -workingdirectory "$bin\AIDA64"
}

if (!(test-path "$logpath\aida64.htm")) {
    WK-write "* Running AIDA64 (Full listing) in background" "$log"
    start "$bin\AIDA64\aida64.exe" -argumentlist @("/R", "$logpath\aida64.html", "/CUSTOM", "$bin\AIDA64\full.rpf", "/HTML", "/SILENT") -workingdirectory "$bin\AIDA64"
}

# SIV
if (!(test-path "$logpath\keys-siv.txt")) {
    WK-write "* Running SIV (Product Keys)" "$log"
    start -wait "$siv" -argumentlist @("-KEYS", "-LOCAL", "-UNICODE", "-SAVE=[product-ids]=$logpath\keys-siv.txt") -workingdirectory "$bin\SIV"
}

if (!(test-path "$logpath\program_list-siv.txt")) {
    WK-write "* Running SIV (SW listing)" "$log"
    start -wait "$siv" -argumentlist @("-KEYS", "-LOCAL", "-UNICODE", "-SAVE=[software]=$logpath\program_list-siv.txt") -workingdirectory "$bin\SIV"
}

if (!(test-path "$logpath\aida64.htm")) {
    WK-write "* Running SIV (Full listing) in background" "$log"
    start -wait "$siv" -argumentlist @("-KEYS", "-LOCAL", "-UNICODE", "-SAVE=$logpath\siv.txt") -workingdirectory "$bin\SIV"
}

# Product Keys
## Extract
md "$bin\tmp" 2>&1 | out-null
start -wait $sz -argumentlist @("e", "$bin\ProduKey.7z", "-otmp", "-aoa", "-pAbracadabra", "-bsp0", "-bso0") -workingdirectory "$bin" -nonewwindow
rm "$bin\tmp\ProduKey*.cfg"
sleep -s 1

## Run
if (!(test-path "$logpath\keys-produkey.txt")) {
    WK-write "* Saving Product Keys" "$log"
    start -wait $produkey -argumentlist @("/nosavereg", "/stext", "$logpath\keys-produkey.txt") -workingdirectory "$bin\tmp"
}

# User Data
WK-write "==== User Data ====" "$log"
& "$wd\user_data.ps1" "$log"
WK-write "" "$log"

# OS Info
WK-write "==== Operating System ====" "$log"
WK-write "  $os_name x$arch" "$log"
WK-write "$win_act" "$log"
if ($win_act -notmatch "permanent") {slui}
WK-write "" "$log"

# Set Timezone and sync clock
WK-write "==== Clock ====" "$log"
start "tzutil" -argumentlist @("/s", '"Pacific Standard Time"') -nonewwindow -redirectstandardoutput out-null
stop-service -name "w32time" 2>&1 | out-null
start "w32tm" -argumentlist @("/config", "/syncfromflags:manual", '/manualpeerlist:"us.pool.ntp.org time.nist.gov time.windows.com"') -nonewwindow -redirectstandardoutput out-null
start-service -name "w32time" 2>&1 | out-null
start "w32tm" -argumentlist "/resync" -nonewwindow -redirectstandardoutput out-null
# gross assumption that tz=PST (should've been set earlier)
WK-write $(get-date -uformat "  %a %Y-%m-%d %H:%m (PST/PDT)") "$log"
WK-write "" "$log"

###  DISABLED FOR NOW ###
## Reset power plans
#WK-write "==== Reset Power Plans ====" "$log"
## Export current power plans
#$pow_backup_path = "$ClientPath\Backups\$date\Power Plans"
#md "$pow_backup_path" > $null 2>&1 | out-null
#$old_power_plans = @()
#foreach ($plan in (powercfg /L)) {
#    if ($plan -imatch '^Power Scheme.*') {
#        $guid = $plan -replace 'Power Scheme GUID:\s+([0-9a-f\-]+).*', '$1'
#        $name = $plan -replace 'Power Scheme GUID:\s+[0-9a-f\-]+\s+\(([^\)]+)\).*', '$1'
#        $set = ($plan -imatch '.*\*$')
#        $old_power_plans += @{GUID = $guid; Name = $name; Set = $set}
#        if (!(test-path "$pow_backup_path\$name.pow")) {
#            powercfg /export "$pow_backup_path\$name.pow" $guid
#        }
#    }
#}
#
#start "powercfg.exe" -argumentlist "-restoredefaultschemes" -nonewwindow -redirectstandardoutput out-null
#WK-write "  All power plans reset to defaults" "$log"
## TODO: Re-add and reset SSD plan(s)
#WK-warn "    If the system has a SSD please verify the correct plan has been selected" "$log"
#WK-write "" "$log"
###  DISABLED FOR NOW ###

# Free Space
WK-write "==== Free Space ====" "$log"
& "$wd\free_space.ps1" "$log"
WK-write "" "$log"

# RAM
WK-write "==== RAM ====" "$log"
& "$wd\installed_ram.ps1" "$log"
WK-write "" "$log"

# Battery Check
WK-write "==== Battery Check ====" "$log"
& "$wd\check_battery.ps1" "$log"
WK-write "" "$log"

## Launch Extra Tools ##
# HWMonitor
if ($arch -eq 64) {
    $prog = "$bin\HWMonitor\HWMonitor64.exe"
} else {
    $prog = "$bin\HWMonitor\HWMonitor.exe"
}
start $prog

# XMPlay
start "$bin\..\Misc\XMPlay.cmd"

## Upload info ##
write-host "Uploading info to NAS..."

# Write batch
$batch = "lcd `"{0}`"`r`n" -f $ClientPath
$batch += "cd `"{0}`"`r`n" -f $diag_dest
$batch += "put -r Info `"{0}`"`r`n" -f $service_order
out-file -encoding "ASCII" -filepath "$wd\psftp_batch" -inputobject $batch

# Upload files
$psftp_args = @(
    "-noagent",
    "-i", "$bin\PuTTY\WK.ppk",
    "$diag_user@$diag_server",
    "-b", "$wd\psftp_batch")
start "$bin\PuTTY\PSFTP.exe" -argumentlist $psftp_args -wait -windowstyle minimized

## Done ##
popd
pause "Press Enter to review drivers and updates..."

# Launch post progs
start devmgmt.msc
if ($win_version -eq 10) {
    start ms-settings:windowsupdate
} else {
    start wuapp
}

# Launch SAS Removal Tool (if necessary)
if ($sas_force_remove) {
	pushd "$bin\_Removal Tools"
    if ($arch -eq 64) {
        $prog = "SASUNINST64.exe"
    } else {
        $prog = "SASUNINST.exe"
    }
    start $prog
	popd
}

# Open log
$notepad2 = "$bin\Notepad2\Notepad2-Mod.exe"
if (test-path "$notepad2") {
    start "$notepad2" -argumentlist $log
} else {
    start "notepad" -argumentlist $log
}
