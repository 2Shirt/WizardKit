# WK-Checklist

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK PE Tool"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\winpe.log"
$source_server = "10.0.0.10"
$backup_servers = @(
    @{  "ip"="10.0.0.10";
        "letter"="Z";
        "name"="ServerOne";
        "path"="Backups"},
    @{  "ip"="10.0.0.11";
        "name"="ServerTwo";
        "letter"="Y";
        "path"="Backups"}
    )
$backup_user = "WORKGROUP\backup"
$backup_pass = "Abracadabra"

# Functions
function apply-image {
    param([string]$image, [int]$index)
    $path = ""
    $split_image = $false
    $split_image_pattern = ""
    
    # Check for local source
    $volumes = get-volume | where {$_.Size -ne 0 -and $_.DriveLetter -match '^[C-Z]$'}
    foreach ($v in $volumes) {
        $letter = $v.DriveLetter + ":"
        if (test-path "$letter\sources\$image.wim") {
            $path = "$letter\sources\$image.wim"
        } elseif (test-path "$letter\sources\$image.swm") {
            $path = "$letter\sources\$image.swm"
            $split_image = $true
            $split_image_pattern = "$letter\sources\$image*.swm"
        }
    }
    
    # Check for remote source (if necessary)
    if ($path -match '^$') {
        net use z: "\\$source_server\Windows" /user:guest notarealpassword
        if (test-path "Z:\$image.wim") {
            $path = "Z:\$image.wim"
        } elseif (test-path "Z:\$image.swm") {
            $path = "Z:\$image.swm"
        }
    }
    
    # Expand Image
    if ($path -match '\.wim$') {
        Expand-WindowsImage -ImagePath "$path" -Index $index -ApplyPath 'W:\'
    } elseif ($path -match '\.swm$') {
        Expand-WindowsImage -ImagePath "$path" -Index $index -ApplyPath 'W:\' -SplitImageFilePattern "$split_image_pattern"
    } else {
        net use z: /delete
        throw "Source image not found."
    }
    net use z: /delete
}
function format-gpt {
    param($dest_disk)
    wk-write "Drive will use a GPT (UEFI) layout."

    # Double-check we have the right drive
    ## I don't trust the order will be the same for diskpart & PS Storage Cmdlets
    $_sel_uid = $dest_disk.Guid
    if ($dest_disk.PartitionStyle -imatch "MBR") {
        # MBR disks don't have GUIDs and use the signature in hex instead
        $_sel_uid = "{0:x}" -f $dest_disk.Signature
    }
    $diskpart_script = "select disk {0}`r`n" -f $dest_disk.DiskNumber
    $diskpart_script += "uniqueid disk"
    out-file -encoding 'UTF8' -filepath "$wd\diskpart.script" -inputobject $diskpart_script
    start "diskpart" -argumentlist @("/s", "$wd\diskpart.script") -wait -nonewwindow -PassThru -RedirectStandardOutput "$wd\drive_uid" | out-null
    if (!(Get-Content "$wd\drive_uid" | where {$_ -imatch $_sel_uid})) {
        # GUIDs do not match
        wk-error "Diskpart failed to select the same disk for formatting, aborting setup."
        wk-warn "This system requires manual formatting & setup"
        wk-write ""
        throw "Failed to format disk"
    } else {
        wk-write ("Selecting Disk {0} ({1})" -f $dest_disk.DiskNumber, $_sel_uid)
    }
    
    # Generate Diskpart script and execute
    ## NOTE 1: PS Storage Cmdlets can't be used; See Keith Garner's response here:
    ## https://social.technet.microsoft.com/Forums/en-US/9d78da31-557f-4408-89e0-a1603f7ebe0d
    ##
    ## NOTE 2: This overwrites existing diskpart.script file without confirmation.
    $diskpart_script = "select disk {0}`r`n" -f $dest_disk.DiskNumber
    $diskpart_script += "clean`r`n"
    $diskpart_script += "convert gpt`r`n"
    
    # 1. Windows RE tools partition (Windows 8+)
    if ($dest_windows_version.Name -match '^Windows (8|10)') {
        $diskpart_script += "create partition primary size=300`r`n"
        $diskpart_script += "format quick fs=ntfs label='Windows RE tools'`r`n"
        $diskpart_script += "assign letter='T'`r`n"
        $diskpart_script += "set id='de94bba4-06d1-4d40-a16a-bfd50179d6ac'`r`n"
        $diskpart_script += "gpt attributes=0x8000000000000001`r`n"
    }
    
    # 2. System partition
    $diskpart_script += "create partition efi size=260`r`n"
    ## NOTE: Allows for Advanced Format 4Kn drives
    $diskpart_script += "format quick fs=fat32 label='System'`r`n"
    $diskpart_script += "assign letter='S'`r`n"
    
    # 3. Microsoft Reserved (MSR) partition
    $diskpart_script += "create partition msr size=128`r`n"
    
    # 4. Windows partition
    $diskpart_script += "create partition primary`r`n"
    $diskpart_script += "format quick fs=ntfs label='Windows'`r`n"
    $diskpart_script += "assign letter='W'`r`n"
    
    # Run script
    out-file -encoding 'UTF8' -filepath "$wd\diskpart.script" -inputobject $diskpart_script
    start "diskpart" -argumentlist @("/s", "$wd\diskpart.script") -wait -nonewwindow
}
function format-mbr {
    param($dest_disk)
    wk-write "Drive will use a MBR (legacy) layout."
    
    if ($dest_disk.PartitionStyle -notmatch '^RAW$') {
        # Only clean if necessary
        clear-Disk $dest_disk.DiskNumber -RemoveData -RemoveOEM -Confirm:$false
    }
    Initialize-Disk $dest_disk.DiskNumber -PartitionStyle 'MBR'
    New-Partition -DiskNumber $dest_disk.DiskNumber -Size 100Mb -DriveLetter 'S' -IsActive:$true
    New-Partition -DiskNumber $dest_disk.DiskNumber -UseMaximumSize -DriveLetter 'W' -IsActive:$false
    Format-Volume -DriveLetter 'S' -FileSystem 'NTFS' -NewFileSystemLabel 'System Reserved'
    Format-Volume -DriveLetter 'W' -FileSystem 'NTFS' -NewFileSystemLabel 'Windows'
}
function wk-exit {
    popd
    if ($answer -match 'R') {
        #pause "Press Enter to Reboot... "
        wpeutil reboot
    } elseif ($answer -match 'S') {
        #pause "Press Enter to Shutdown... "
        wpeutil shutdown
    }
    exit 0
}
function mount-servers {
    # Mount servers
    wk-write "Connecting to backup server(s)"
    foreach ($_server in $backup_servers) {
        if (test-connection $_server.ip -count 1 -quiet 2>&1 | out-null) {
            try {
                $_path = "\\{0}\{1}" -f $_server.ip, $_server.path
                $_drive = "{0}:" -f $_server.letter
                net use $_drive "$_path" /user:$backup_user $backup_pass | out-null
                wk-write ("`t{0} server: mounted" -f $_server.name)
                
                # Add friendly description
                $_regex = "^{0}$" -f $_server.letter
                (gdr | where {$_.Name -imatch $_regex}).Description = $_server.name
            } catch {
                wk-warn ("`t{0} server: failed" -f $_server.name)
            }
        } else {
            wk-warn ("`t{0} server: unreachable" -f $_server.name)
        }
    }
}
function unmount-servers {
    # Unmount servers
    wk-write "Disconnecting from backup server(s)"
    $mounted_servers = @(gdr | where {$_.DisplayRoot -imatch '\\\\'})
    foreach ($_server in $mounted_servers) {
        try {
            $_drive = "{0}:" -f $_server.Name
            net use $_drive /delete | out-null
            wk-warn ("`t{0} server: unmounted" -f $_server.name)
        } catch {
            wk-warn ("`t{0} server: failed" -f $_server.name)
        }
    }
}
function menu-imaging {
    wk-write "Drive Imaging"
    wk-write ""
    
    ## WARNING
    wk-warn "WARNING: This section is experimental"
    pause
    ## WARNING
    
    # Check if any source drives were detected
    $disks = get-disk | where {$_.Size -ne 0}
#    if ($disks.count -eq 0) {
#        wk-error "No suitable source drives were detected."
#        pause "Press Enter to return to main menu... " $True
#        return 1
#    }
    
    # Mount server(s)
    mount-servers
    
    # Build server menu
    $avail_servers = @(gdr | where {$_.DisplayRoot -imatch '\\\\'})
#    if ($avail_servers.count -eq 0) {
#        wk-error "No suitable backup servers were detected."
#        pause "Press Enter to return to main menu... " $True
#        return 1
#    }
    $menu_imaging_server = "Where are we saving the backup image(s)?`r`n`r`n"
    $valid_answers = @("M", "m")
    for ($i=0; $i -lt $avail_servers.length; $i++) {
        $valid_answers += ($i + 1)
        $menu_imaging_server += ("{0}: {1} ({2:N2} Gb free)`r`n" -f ($i + 1), $avail_servers[$i].Description, ($avail_servers[$i].Free / 1Gb))
    }
    $menu_imaging_server += "`r`n"
    $menu_imaging_server += "M: Main Menu`r`n"
    $menu_imaging_server += "`r`n"
    $menu_imaging_server += "Please make a selection`r`n"
    
    # Select server
    do {
##testing##        clear
        $answer = read-host -prompt $menu_imaging_server
    } until ($valid_answers -contains $answer)
    if ($answer -imatch '^M$') {
        # Exit if requested
        unmount-servers
        return
    } else {
        $answer -= 1
        $dest_backup_server = $avail_servers[$answer]
    }
    
    # Build source menu
    $menu_imaging_source = "For which drive are we creating backup image(s)?`r`n`r`n"
    $valid_answers = @("M", "m")
    foreach ($_ in $disks) {
        $valid_answers += $_.DiskNumber
        $menu_imaging_source += "{0}: {1:N0} Gb`t({2}) {3} ({4})`r`n" -f $_.DiskNumber, ($_.Size / 1GB), $_.BusType, $_.FriendlyName, $_.PartitionStyle
    }
    $menu_imaging_source += "`r`n"
    $menu_imaging_source += "M: Main Menu`r`n"
    $menu_imaging_source += "`r`n"
    $menu_imaging_source += "Please make a selection`r`n"
    
    # Select source
    do {
##testing##        clear
        $answer = read-host -prompt $menu_imaging_source
    } until ($valid_answers -contains $answer)
    
    if ($answer -imatch '^M$') {
        # Exit if requested
        return
    } else {
        ##TODO##
        get-volume
    }
    
    # Service Order
    $menu_service_order += "Please enter the service order`r`n"
    do {
##testing##        clear
        $service_order = read-host -prompt $menu_service_order
    } until ($service_order -imatch '^\d[\w\-]+$')
    
    # Backup partitions
    wk-write ("Saving partition backups to: {0}" -f $dest_backup_server.Description)
    wk-write ("`t{0}{1}" -f $dest_backup_server.Root, $service_order)
    
    # Unmount server(s)
    unmount-servers
    pause "Press Enter to return to main menu... "
}
function menu-setup {
    wk-write "Windows Setup"
    wk-write ""
    
    # Check if any destination drives were detected
    $disks = get-disk | where {$_.Size -ne 0 -and $_.BusType -inotmatch 'USB'}
    if ($disks.count -eq 0) {
        wk-error "No suitable destination drives were detected."
        pause "Press Enter to return to main menu... " $True
        return 1
    }
    
    # Build windows menu
    $windows_versions = @(
        @{Name="Windows 7 Home Premium"; ImageFile="Win7"; Index=1},
        @{Name="Windows 7 Professional"; ImageFile="Win7"; Index=2},
        @{Name="Windows 7 Ultimate"; ImageFile="Win7"; Index=3},
        @{Name="Windows 8.1"; ImageFile="Win8"; Index=1},
        @{Name="Windows 8.1 Pro"; ImageFile="Win8"; Index=2},
        @{Name="Windows 10 Home"; ImageFile="Win10"; Index=1},
        @{Name="Windows 10 Pro"; ImageFile="Win10"; Index=2}
    )
    $menu_setup_windows = "Which version of Windows are we installing?`r`n`r`n"
    $valid_answers = @("M", "m")
    for ($i=0; $i -lt $windows_versions.length; $i++) {
        $valid_answers += ($i + 1)
        $menu_setup_windows += "{0}: {1}`r`n" -f ($i + 1), $windows_versions[$i].Name
    }
    $menu_setup_windows += "`r`n"
    $menu_setup_windows += "M: Main Menu`r`n"
    $menu_setup_windows += "`r`n"
    $menu_setup_windows += "Please make a selection`r`n"
    
    # Select Windows version
    do {
##testing##        clear
        $answer = read-host -prompt $menu_setup_windows
    } until ($valid_answers -contains $answer)
    
    if ($answer -imatch '^M$') {
        # Exit if requested
        return
    } else {
        $answer -= 1
        $dest_windows_version = $windows_versions[$answer]
    }
    
    # Build disk menu
    $menu_setup_disk = "To which drive are we installing {0}?`r`n`r`n" -f $dest_windows_version.Name
    $valid_answers = @("M", "m")
    foreach ($_ in $disks) {
        $valid_answers += $_.DiskNumber
        $menu_setup_disk += "{0}: {1:N0} Gb`t({2}) {3}`r`n" -f $_.DiskNumber, ($_.Size / 1GB), $_.PartitionStyle, $_.FriendlyName
    }
    $menu_setup_disk += "`r`n"
    $menu_setup_disk += "M: Main Menu`r`n"
    $menu_setup_disk += "`r`n"
    $menu_setup_disk += "Please make a selection`r`n"
    
    # Select disk
    do {
##testing##        clear
        $answer = read-host -prompt $menu_setup_disk
    } until ($valid_answers -contains $answer)
    
    if ($answer -imatch '^M$') {
        # Exit if requested
        return
    } else {
        # Double check before deleting data
        $dest_disk = $disks | where {$_.DiskNumber -eq $answer}
        wk-warn "All data will be deleted from the following drive:"
        wk-warn ("`t{0:N0} Gb`t({1}) {2}`r`n" -f ($dest_disk.Size / 1GB), $dest_disk.PartitionStyle, $dest_disk.FriendlyName)
        if (ask ("Proceed and install {0}?" -f $dest_windows_version.Name)) {
            wk-warn "SAFTEY CHECK:"
            wk-write ("  Installing:`t{0}" -f $dest_windows_version.Name)
            wk-error ("  And ERASING:`tDisk {0} - {1:N0} Gb`t({2}) {3}`r`n" -f $dest_disk.DiskNumber, ($dest_disk.Size / 1GB), $dest_disk.PartitionStyle, $dest_disk.FriendlyName)
            if (ask "Is this correct?") {
                ## WARNING
                wk-warn "WARNING: This section is experimental"
                ## WARNING
                ## Here be dragons
                
                try {
                    # Select UEFI or BIOS
                    if ($dest_windows_version.Name -match '^Windows 7') {
                        if (ask "Setup drive using MBR (legacy) layout?") {
                            format-mbr $dest_disk
                        } else {
                            format-gpt $dest_disk
                        }
                    } elseif ($dest_windows_version.Name -match '^Windows (8|10)') {
                        if (ask "Setup drive using GPT (UEFI) layout?") {
                            format-gpt $dest_disk
                        } else {
                            format-mbr $dest_disk
                        }
                    }
                    
                    # Apply image
                    apply-image $dest_windows_version.ImageFile $dest_windows_version.Index
                
                    # Create boot files (copies files for both Legacy and UEFI)
                    bcdboot W:\Windows /s S: /f ALL
                    if ($dest_windows_version.Name -match '^Windows (8|10)') {
                        W:\Windows\System32\reagentc /setreimage /path T:\Recovery\WindowsRE /target W:\Windows
                    }
                    
                    # Reboot
                    wk-write "Windows Setup complete."
                    wk-write ""
                    return 0
                } catch {
                    wk-error "$Error"
                    wk-error "Windows Setup aborted."
                    wk-write ""
                    pause "Press Enter to return to main menu... "
                    return 1
                }
            } else {
                wk-error "Windows Setup aborted."
                wk-write ""
                pause "Press Enter to return to main menu... "
            }
        } else {
            wk-error "Windows Setup aborted."
            wk-write ""
            pause "Press Enter to return to main menu... "
        }
    }
}
function menu-tools {
    wk-write "Misc Tools"
    wk-write ""
    wk-warn "Be careful."
    start "$WKPath\explorer++" -argumentlist @("$WKPath")
    wk-exit
}
function menu-main {
    $answered = $false
    $menu_main = @"
WK WinPE Tools

1: Drive Imaging
2: Windows Setup
3: Misc Tools

Q: Quit
R: Reboot
S: Shutdown

Please make a selection
"@

    do {
##testing##        clear
        $answer = read-host -prompt $menu_main
    } until ($answer -imatch '^[123QRS]$')
##testing##    clear

    if ($answer.GetType().Name -match "String") {
        $answer = $answer.ToUpper()
    }
    switch ($answer) {
        1 {menu-imaging; break}
        2 {menu-setup; break}
        3 {menu-tools; break}
        default {wk-exit}
    }
}

# Main Loop
do {
    menu-main
} while ($true)
