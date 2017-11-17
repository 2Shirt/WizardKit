# Wizard Kit: Software Diagnostics

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Diagnostics Tool"
$backup_path = "$ClientPath\Backups\$username\$date"
$logpath = "$ClientPath\Info\$date"
md "$backup_path" 2>&1 | out-null
md "$logpath" 2>&1 | out-null
$log = "$logpath\Diagnostics.log"
$bin = (Get-Item $wd).Parent.FullName
$diag_dest = "/srv/Diagnostics"
$diag_server = "10.0.0.10"
$diag_user = "wkdiag"
$conemu = "$bin\ConEmu\ConEmu.exe"
$sz = "$bin\7-Zip\7za.exe"
$produkey = "$bin\tmp\ProduKey.exe"
$siv = "$bin\SIV\SIV.exe"

# OS Check
. .\check_os.ps1
if ($arch -eq 64) {
    $conemu = "$bin\ConEmu\ConEmu64.exe"
    $sz = "$bin\7-Zip\7za64.exe"
    $produkey = "$bin\tmp\ProduKey64.exe"
    $siv = "$bin\SIV\SIV64.exe"
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
WK-write "Starting SW diagnostics for Ticket #$service_order" "$log"
WK-write "" "$log"

## Sanitize Environment ##
#~# BROKEN #~#
#~# # ProcessKiller
#~# #   adapted from TronScript (reddit.com/r/TronScript) and credit to /u/cuddlychops06
#~# #WK-write "* Stopping all processes" "$log"
#~# taskkill.exe /F /FI "USERNAME eq Demo" /FI "IMAGENAME ne ClassicShellService.exe" /FI "IMAGENAME ne explorer.exe" /FI "IMAGENAME ne dwm.exe" /FI "IMAGENAME ne cmd.exe" /FI "IMAGENAME ne Taskmgr.exe" /FI "IMAGENAME ne MsMpEng.exe" /FI "IMAGENAME ne powershell.exe" /FI "IMAGENAME ne rkill.exe" /FI "IMAGENAME ne rkill64.exe" /FI "IMAGENAME ne rkill.com" /FI "IMAGENAME ne rkill64.com" /FI "IMAGENAME ne conhost.exe" /FI "IMAGENAME ne dashost.exe" /FI "IMAGENAME ne vmtoolsd.exe" /FI "IMAGENAME ne conhost.exe" 2>&1 | out-null

# RKill
WK-write "* Running RKill" "$log"
start -wait "$conemu" -argumentlist @("/cmd", "$bin\RKill\RKill.exe", "-l", "$logpath\rkill.log")
if (!(ask "Did RKill run correctly?" "$log")) {
    start -wait "$conemu" -argumentlist @("/cmd", "$bin\RKill\explorer.exe", "-l", "$logpath\rkill.log")
    if (!(ask "Did RKill run correctly?" "$log")) {
        WK-warn "Since RKill has failed to run, please try an alternative version." "$log"
        WK-warn "Opening RKill folder..." "$log"
        WK-write "" "$log"
        sleep -s 2
        ii "$bin\RKill\"
        pause
    }
}

# TDSSKiller Rootkit scan
WK-write "* Running Rootkit scan" "$log"
if (test-path "$bin\TDSSKiller.exe") {
    md "$ClientPath\Quarantine\TDSSKiller" 2>&1 | out-null
    start -wait "$bin\TDSSKiller.exe" -argumentlist @("-l", "$logpath\TDSSKiller.log", "-qpath", "$ClientPath\Quarantine\TDSSKiller", "-accepteula", "-accepteulaksn", "-dcexact", "-tdlfs")
} else {
    WK-error "  TDSSKiller.exe missing. Please verify Wizard-Kit was copied correctly."
}

## Network Check ##
WK-write "* Testing Internet Connection" "$log"
while (!(test-connection "google.com" -count 2 -quiet)) {
    WK-warn "System appears offline. Please connect to the internet." "$log"
    if (!(ask "Try again?" "$log")) {
        WK-error "System still appears offline; aborting script." "$log"
        exit 1
    }
}

## Misc Configuration ##
# Export current power plans
$pow_backup_path = "$ClientPath\Backups\$date\Power Plans"
md "$pow_backup_path" > $null 2>&1 | out-null
foreach ($plan in (powercfg /L)) {
    if ($plan -imatch '^Power Scheme.*') {
        $guid = $plan -replace 'Power Scheme GUID:\s+([0-9a-f\-]+).*', '$1'
        $name = $plan -replace 'Power Scheme GUID:\s+[0-9a-f\-]+\s+\(([^\)]+)\).*', '$1'
        $set = ($plan -imatch '.*\*$')
        if (!(test-path "$pow_backup_path\$name.pow")) {
            powercfg /export "$pow_backup_path\$name.pow" $guid
        }
    }
}

# Change Power Plan
WK-write "* Changing power plan to 'High Performance'" "$log"
start "powercfg.exe" -argumentlist @("-restoredefaultschemes") -nonewwindow -redirectstandardoutput out-null
start -wait "powercfg" -argumentlist @("-setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c") -nonewwindow -redirectstandardoutput out-null

## Begin Diagnostics ##
# Infection Scan
WK-write "* Starting background infection scan" "$log"
if ($arch -eq 64) {
    $prog = "$bin\HitmanPro\HitmanPro64.exe"
} else {
    $prog = "$bin\HitmanPro\HitmanPro.exe"
}
start $prog -argumentlist @("/quiet", "/noinstall", "/noupload", "/log=$logpath\hitman.xml") -workingdirectory "$bin\HitmanPro"

#~# BROKEN #~#
#~# # OS Health Checks
#~# ## DISM
#~# if ($win_version -match '^8|10$') {
#~#     start "$conemu" -argumentlist @("/cmd", "$windir\System32\dism.exe", "/online", "/cleanup-image", "/checkhealth", "/logpath:$logpath\DISM.log", "-new_console:c")
#~# }
#~# ## SFC
#~# start "$conemu" -argumentlist @("/cmd", "$windir\System32\sfc.exe", "/scannow", "-new_console:c")
#~# ## CHKDSK
#~# start "$conemu" -argumentlist @("/cmd", "$windir\System32\chkdsk.exe", "$systemdrive", "-new_console:c")

# Backup Registry
if (!(test-path "$logpath\Registry")) {
    WK-write "* Backing up registry" "$log"
    start -wait "$bin\Erunt\ERUNT.EXE" -argumentlist @("$logpath\Registry", "sysreg", "curuser", "otherusers", "/noprogresswindow") -workingdirectory "$bin\Erunt"
}

# Backup Browsers
if (test-path "$localappdata\Google\Chrome") {
    WK-write "* Backing up Google Chrome" "$log"
    pushd "$localappdata\Google\Chrome"
    $sz_args = @(
        "a", "-t7z", "-mx=1",
        "$backup_path\Chrome.7z",
        '"User Data"')
    start $sz -argumentlist $sz_args -wait -windowstyle minimized
    popd
}
if (test-path "$appdata\Mozilla\Firefox") {
    WK-write "* Backing up Mozilla Firefox" "$log"
    pushd "$appdata\Mozilla\Firefox"
    $sz_args = @(
        "a", "-t7z", "-mx=1",
        "$backup_path\Firefox.7z",
        "Profiles",
        "profiles.ini")
    start $sz -argumentlist $sz_args -wait -windowstyle minimized
    popd
}
if (test-path "$userprofile\Favorites") {
    WK-write "* Backing up Internet Explorer" "$log"
    pushd "$userprofile"
    $sz_args = @(
        "a", "-t7z", "-mx=1",
        "$backup_path\IE Favorites.7z",
        "Favorites")
    start $sz -argumentlist $sz_args -wait -windowstyle minimized
    popd
}

# Get total size of temporary files
if (!(test-path "$logpath\bleachbit.log")) {
    WK-write "* Checking for temporary files" "$log"
    start -wait "$bin\BleachBit\bleachbit_console.exe" -argumentlist @("--preview", "--preset") -nonewwindow -workingdirectory "$bin\BleachBit" -redirectstandarderror "$logpath\bleachbit.err" -redirectstandardoutput "$logpath\bleachbit.log"
}

# Autoruns
if (!(test-path "$logpath\autoruns.arn")) {
    WK-write "* Starting background autoruns scan" "$log"
    New-Item -Path "HKCU:\Software\Sysinternals\AutoRuns" -Force 2>&1 | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "checkvirustotal" -Value 1 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "EulaAccepted" -Value 1 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "shownomicrosoft" -Value 1 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "shownowindows" -Value 1 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "showonlyvirustotal" -Value 1 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "submitvirustotal" -Value 0 -Type "DWord" | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns" -Name "verifysignatures" -Value 1 -Type "DWord" | out-null
    New-Item "HKCU:\Software\Sysinternals\AutoRuns\SigCheck" 2>&1 | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns\SigCheck" -Name "EulaAccepted" -Value 1 -Type "DWord" | out-null
    New-Item "HKCU:\Software\Sysinternals\AutoRuns\Streams" 2>&1 | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns\Streams" -Name "EulaAccepted" -Value 1 -Type "DWord" | out-null
    New-Item "HKCU:\Software\Sysinternals\AutoRuns\VirusTotal" 2>&1 | out-null
    Set-ItemProperty -Path "HKCU:\Software\Sysinternals\AutoRuns\VirusTotal" -Name "VirusTotalTermsAccepted" -Value 1 -Type "DWord" | out-null
    start "$bin\SysinternalsSuite\autoruns.exe" -workingdirectory "$bin\SysinternalsSuite" -windowstyle "minimized"
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

## Summary ##
WK-write "" "$log"

# Removed temp file size
WK-write "==== Temp Files ====" "$log"
$bb = (gc "$logpath\bleachbit.log") -imatch '^(disk space.*recovered|files.*deleted)'
foreach ($_ in $bb) {
    $_ = "  " + $_
    WK-write $_ "$log"
}
WK-write "" "$log"

# Free Space
WK-write "==== Free Space ====" "$log"
& "$wd\free_space.ps1" "$log"
WK-write "" "$log"

# RAM
WK-write "==== RAM ====" "$log"
& "$wd\installed_ram.ps1" "$log"
WK-write "" "$log"

# List installed Office programs
WK-write "==== Installed Office Programs ====" "$log"
$installed_office = (gc "$logpath\program_list-aida64.txt") -imatch 'Office' | sort
foreach ($_ in $installed_office) {
    $_ = $_ -ireplace '^\s+(.*?)\s\s+.*', '$1'
    WK-write "  $_" "$log"
}
WK-write "" "$log"

# Saved keys
WK-write "==== Found Product Keys ====" "$log"
$keys = (gc "$logpath\keys-produkey.txt") -imatch '(product.name)'
foreach ($_ in $keys) {
    $_ = $_ -ireplace '^product name\s+: ', '  '
    WK-write $_ "$log"
}
WK-write "" "$log"


# OS Info
WK-write "==== Operating System ====" "$log"
if ($arch -eq 32) {
    WK-error "  $os_name x$arch" "$log"
} elseif ($win_info.CurrentVersion -match "6.0") {
    if ($win_info.CurrentBuildNumber -match "6002") {
        WK-warn "  $os_name x$arch" "$log"
    } elseif ($win_info.CurrentBuildNumber -match "6001") {
        WK-error "  $os_name x$arch (very out of date)" "$log"
    } elseif ($win_info.CurrentBuildNumber -match "6000") {
        WK-error "  $os_name x$arch (very out of date)" "$log"
    }
} elseif ($win_info.CurrentVersion -match "6.2") {
    WK-error "  $os_name x$arch (very out of date)" "$log"
} elseif ($win_info.CurrentBuildNumber -match "10240") {
    WK-error "  $os_name x$arch (Release 1511 not installed)" "$log"
} else {
    WK-write "  $os_name x$arch" "$log"
}
if ($win_act -imatch 'unavailable') {
    WK-warn "$win_act" "$log"
} elseif ($win_act -notmatch "permanent") {
    WK-error "$win_act" "$log"
} else {
    WK-write "$win_act" "$log"
}
WK-write "" "$log"

# Updates Check
# TODO: Finish and test this
#WK-write "==== Windows Updates ====" "$log"
#import-module "$bin\Scripts\PSWindowsUpdate"
# Check last install date
#get-wuhistory | sort-object date -descending | select-object -first 1
# Check if installs CS
#   TODO
# Return avail updates
#get-wulist
#WK-write "" "$log"

# Battery Check 
WK-write "==== Battery Check ====" "$log"
& "$wd\check_battery.ps1" "$log"
WK-write "" "$log"

# User Data
WK-write "==== User Data ====" "$log"
& "$wd\user_data.ps1" "$log"
WK-write "" "$log"

# Upload info
write-host "Uploading info to NAS..."

## Write batch
$batch = "lcd `"{0}`"`r`n" -f $ClientPath
$batch += "cd `"{0}`"`r`n" -f $diag_dest
$batch += "put -r Info `"{0}`"`r`n" -f $service_order
out-file -encoding "ASCII" -filepath "$wd\psftp_batch" -inputobject $batch

## Upload files
$psftp_args = @(
    "-noagent",
    "-i", "$bin\PuTTY\WK.ppk",
    "$diag_user@$diag_server",
    "-b", "$wd\psftp_batch")
start "$bin\PuTTY\PSFTP.exe" -argumentlist $psftp_args -wait -windowstyle minimized

## Done ##
popd
pause "Press Enter to exit..."

# Open log
$notepad2 = "$bin\Notepad2\Notepad2-Mod.exe"
if (test-path $notepad2) {
    start "$notepad2" -argumentlist $log
} else {
    start "notepad" -argumentlist $log
}
