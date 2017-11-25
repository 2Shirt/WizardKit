# WK imaging functions

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1

# Functions
function apply-image {
    # Apply a Windows image to W:\
    Param([string]$image, [string]$name)
    $path = ""
    $split_image = $false
    $split_image_pattern = ""
    
    # Check for source image
    ##  This checks all drive letters for the source image.
    ##  It starts with local sources and then tries the server(s) (usually Y: and Z:)
    $volumes = @(Get-Volume | Where-Object {$_.Size -ne 0 -and $_.DriveLetter -imatch '^[C-Z]$'})
    foreach ($v in $volumes) {
        $letter = $v.DriveLetter + ":"
        if (Test-Path "$letter\sources\$image.wim") {
            $path = "$letter\sources\$image.wim"
        } elseif (Test-Path "$letter\sources\$image.esd") {
            $path = "$letter\sources\$image.esd"
        } elseif (Test-Path "$letter\sources\$image.swm") {
            $path = "$letter\sources\$image.swm"
            $split_image = $true
            $split_image_pattern = "$letter\sources\$image*.swm"
        }
    }
    
    # Check for FQDN remote source (if necessary)
    if ($path -imatch '^$') {
        # Temporarily set path to network source
        $path = "\\$source_server\Windows\$image"
        wk-warn "Searching for network source"
        if (Test-Path "$path.wim") {
            $path = "$path.wim"
        } elseif (Test-Path "$path.esd") {
            $path = "$path.esd"
        } elseif (Test-Path "$path.swm") {
            $path = "$path.swm"
            $split_image = $true
            $split_image_pattern = "$path*.swm"
        } else {
            # Revert to empty path if nothing found.
            $path = ""
        }
    }
    
    # Expand Image
    if ($path -imatch 'Win\d+\.(esd|wim)$') {
        wk-write "  Applying image..."
        Expand-WindowsImage -ImagePath "$path" -Name "$name" -ApplyPath 'W:\' | out-null
    } elseif ($path -imatch 'Win\d+\.swm$') {
        wk-write "  Applying split-image..."
        Expand-WindowsImage -ImagePath "$path" -Name "$name" -ApplyPath 'W:\' -SplitImageFilePattern "$split_image_pattern" | out-null
    } else {
        wk-error "Image not found."
        throw
    }
}
function format-gpt {
    Param($dest_disk)
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
    Out-File -encoding 'UTF8' -filepath "$wd\diskpart.script" -inputobject $diskpart_script
    Start-Process "diskpart" -argumentlist @("/s", "$wd\diskpart.script") -wait -nonewwindow -PassThru -RedirectStandardOutput "$wd\drive_uid" | Out-Null
    if (!(Get-Content "$wd\drive_uid" | Where-Object {$_ -imatch $_sel_uid})) {
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
    if ($dest_windows_version.Name -imatch '^Windows (8|10)') {
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
    Out-File -encoding 'UTF8' -filepath "$wd\diskpart.script" -inputobject $diskpart_script
    Start-Process "diskpart" -argumentlist @("/s", "$wd\diskpart.script") -wait -nonewwindow | out-null
}
function format-mbr {
    Param($dest_disk)
    wk-write "Drive will use a MBR (legacy) layout."
    
    if ($dest_disk.PartitionStyle -inotmatch '^RAW$') {
        # Only clean if necessary
        clear-Disk $dest_disk.DiskNumber -RemoveData -RemoveOEM -Confirm:$false | out-null
    }
    Initialize-Disk $dest_disk.DiskNumber -PartitionStyle 'MBR' | out-null
    New-Partition -DiskNumber $dest_disk.DiskNumber -Size 100Mb -DriveLetter 'S' -IsActive:$true | out-null
    New-Partition -DiskNumber $dest_disk.DiskNumber -UseMaximumSize -DriveLetter 'W' -IsActive:$false | out-null
    Format-Volume -DriveLetter 'S' -FileSystem 'NTFS' -NewFileSystemLabel 'System Reserved' | out-null
    Format-Volume -DriveLetter 'W' -FileSystem 'NTFS' -NewFileSystemLabel 'Windows' | out-null
}
function select-disk {
    param([string]$title, [bool]$skip_usb=$false)
    $_skipped_parts = 0
        
    # Get Disk(s)
    if ($skip_usb) {
        $disks = @(Get-Disk | Where-Object {$_.Size -ne 0 -and $_.BusType -inotmatch 'USB'} | Sort-Object -Property "Number")
    } else {
        $disks = @(Get-Disk | Where-Object {$_.Size -ne 0} | Sort-Object -Property "Number")
    }
    
    # Check if any drives were detected
    if ($disks.count -eq 0) {
        wk-error "No suitable drives were detected."
        return $false
    }
    
    # Get selection
    $selection = $null
    $main_set = @()
    if ($disks.count -eq 1) {
        # Only one disk is available
        $selection = $disks[0]
    } else {
        # Multiple options. Build and use menu
        foreach ($_ in $disks) {
            $_entry = "{0}`t[{1}] ({2}) {3}" -f (human-size $_.Size 0), $_.PartitionStyle, $_.BusType, $_.FriendlyName
            $main_set += @{Name=$_entry}
        }
        $actions = @(@{Name="Main Menu"; Letter="M"})
        $selection = (menu-select $title $main_set $actions)
    }
    
    if ($selection -imatch '^\d+$') {
        $selection -= 1
        return $disks[$selection]
    } else {
        return $selection
    }
}
function menu-imaging {
    wk-write "Drive Imaging"
    wk-write ""

    # Pre-emptively mount Server(s)
    ##  Helps ensure a successfull backup and/or setup
    mount-servers
    
    ## WARNING
    wk-warn "WARNING: This section is experimental"
    pause
    ## WARNING

    # Service Order
    $menu_service_order += "Please enter the service order`r`n"
    do {
        clear
        $service_order = read-host -prompt $menu_service_order
    } until ($service_order -imatch '^\d[\w\-]+$')
    
    # Select Disk
    $disk = (select-disk "For which drive are we creating backup image(s)?")
    
    if (!($disk)) {
        # No drives detected or user aborted
        wk-warn "Drive Imaging aborted."
        wk-write ""
        pause "Press Enter to return to main menu... " -warning=$true
        return $false
    } elseif ($disk -imatch '^M$') {
        # User selected to return to the menu
        return $false
    } elseif ($disk.DiskNumber -imatch '^\d+$') {
        # Valid disk selected
        clear
        wk-write ("Disk:`t{0}`t[{1}] ({2}) {3}" -f (human-size $disk.Size 0), $disk.PartitionStyle, $disk.BusType, $disk.FriendlyName)
        wk-write "Partition(s):"
        
        # Print partition info
        $partitions = Get-Partition -DiskNumber $disk.DiskNumber
        $_skipped_parts = 0
        foreach ($_p in $partitions) {
            # Assign letter
            Add-PartitionAccessPath -DiskNumber $disk.DiskNumber -PartitionNumber $_p.PartitionNumber -AssignDriveLetter 2>&1 | Out-Null
            
            # Update partition info
            $_p = Get-Partition -DiskNumber $disk.DiskNumber -PartitionNumber $_p.PartitionNumber
            $_v = Get-Volume -Partition $_p
            
            # Set size label
            $_size = (human-size $_p.size 0)
            $_used = ""
            if ($_v) {
                $_used = "({0} used)" -f (human-size ($_v.Size - $_v.SizeRemaining) 0)
            }
            
            # Print partition info
            if ($_p.AccessPaths) {
                # Has drive letter
                $_path = $_p.AccessPaths | Where-Object {$_ -imatch '^\w:\\$'}
                $_label = " {0}" -f $_p.Type
                if ($_v -and $_v.FileSystemLabel -ne "") {
                    $_label = '"{0}"' -f $_v.FileSystemLabel
                }
                $_msg = "    {0:N0}:`t{1} ({2,6}) {3} {4}" -f $_p.PartitionNumber, $_path, $_size, $_label, $_used
                wk-write "$_msg"
            } else {
                # No drive letter
                $_msg = "   *{0:N0}:`t    ({1})  {2}" -f $_p.PartitionNumber, $_size, $_p.Type
                wk-error "$_msg"
                $_skipped_parts += 1
            }
        }
        if ($_skipped_parts -gt 0) {
            wk-warn "   *`tUnable to backup these partition(s)"
        }
        wk-write ""
        if (!(ask "    Backup these partition(s)?")) {
            wk-warn "Drive Imaging aborted."
            wk-write ""
            pause "Press Enter to return to main menu... " -warning=$true
            return $false
        }
    }
    wk-write ""
    
    # Select Server
    $server = (select-server)
    if (!($server)) {
        # No servers detected
        wk-warn "Drive Imaging aborted."
        wk-write ""
        pause "Press Enter to return to main menu... " -warning=$true
        return $false
    } elseif ($server -imatch '^M$') {
        # User selected to return to the menu
        return
    }
    wk-write ""
    wk-write ("Saving partition backups to: {0}" -f $server.Description)
    wk-write ""
    
    # Backup partitions
    $partitions = Get-Partition -DiskNumber $disk.DiskNumber
    foreach ($_p in $partitions) {
        $_v = Get-Volume -Partition $_p
        
        $_name = "{0}" -f $_p.PartitionNumber
        if ($_v -and $_v.FileSystemLabel -ne "") {
            $_name += "_{0}" -f $_v.FileSystemLabel
        } else {
            $_name += "_{0}" -f $_p.Type
        }
        # Sanitize the name
        $_name = $_name -replace '\s', '_'
        
        $_imagepath = "{0}{1}" -f $server.Root, $service_order
        $_imagefile = "{0}{1}\{2}.wim" -f $server.Root, $service_order, $_name
        
        if ($_p.AccessPaths -ne $null) {
            # Avoid unwanted clobbering
            if (Test-Path "$_imagefile") {
                if (!(ask ("Overwrite backup image: {0}" -f $_imagefile))) {
                    wk-warn "Drive Imaging aborted."
                    wk-write ""
                    pause "Press Enter to return to main menu... " -warning=$true
                    return $false
                }
            }
            $_capturedir = $_p.AccessPaths | Where-Object {$_ -imatch '^\w:\\$'}
            
            # Take image
            wk-write ("    Imaging partition {0} --> `"{1}`"" -f $_p.PartitionNumber, $_imagefile)
            if (!(Test-Path "$_imagepath")) {
                mkdir "$_imagepath" | out-null
            }
            $_dism_args = @(
                "/Capture-Image",
                "/ImageFile:$_imagefile",
                "/CaptureDir:$_capturedir",
                "/Name:$_name",
                "/Compress:fast",
                "/Quiet")
            Start-Process "$windir\System32\Dism.exe" -ArgumentList $_dism_args -NoNewWindow -Wait | out-null
            
            ## The following command fails to capture OS partitions consitantly. Until this is fixed I will use DISM directly (as above).
            #New-WindowsImage -ImagePath "$_imagefile" -CapturePath "$_capturedir" -Name "$_name" -CompressionType "fast" | out-null
            
            # Verify image
            ## Code borrowed from: https://stackoverflow/a/10262275
            $pinfo = New-Object System.Diagnostics.ProcessStartInfo
            $pinfo.FileName = "$WKPath\7-Zip\7z.exe"
            $pinfo.RedirectStandardError = $true
            $pinfo.RedirectStandardOutput = $true
            $pinfo.UseShellExecute = $false
            $pinfo.Arguments = 't "{0}"' -f $_imagefile
            $p = New-Object System.Diagnostics.Process
            $p.StartInfo = $pinfo
            $p.Start() | Out-Null
            write-host "      Verifying . . . " -NoNewline
            $p.WaitForExit()
            if ($p.ExitCode -eq 0) {
                write-host "Complete." -foreground "green"
            } else {
                write-host "Failed." -foreground "red"
            }
        }
    }
    pause "Press Enter to return to main menu... "
}
function menu-setup {
    # Pre-emptively mount Server(s)
    ##  Helps ensure a successfull backup and/or setup
    mount-servers
    
    # Select Disk
    $dest_disk = (select-disk "To which drive are we installing Windows?" -skip_usb=$true)
    
    if (!($dest_disk)) {
        # No drives detected or user aborted
        wk-warn "Windows Setup aborted."
        wk-write ""
        pause "Press Enter to return to main menu... " -warning=$true
        return $false
    } elseif ($dest_disk -imatch '^M$') {
        # User selected to return to the menu
        return $false
    } elseif ($dest_disk.DiskNumber -inotmatch '^\d+$') {
        # This shouldn't happen?
        throw
    } else {
        wk-warn "All data will be deleted from the following drive:"
        wk-warn ("`t{0}`t({1}) {2}`r`n" -f (human-size $dest_disk.Size 0), $dest_disk.PartitionStyle, $dest_disk.FriendlyName)
        if (!(ask "Proceed and install Windows?")) {
            wk-warn "Windows Setup aborted."
            wk-write ""
            pause "Press Enter to return to main menu... " -warning=$true
            return $false
        }
    }
    
    # Set available Windows versions
    $windows_versions = @(
        @{Name="Windows 7 Home Basic"; ImageFile="Win7"; ImageName="Windows 7 HOMEBASIC"}
        @{Name="Windows 7 Home Premium"; ImageFile="Win7"; ImageName="Windows 7 HOMEPREMIUM"}
        @{Name="Windows 7 Professional"; ImageFile="Win7"; ImageName="Windows 7 PROFESSIONAL"}
        @{Name="Windows 7 Ultimate"; ImageFile="Win7"; ImageName="Windows 7 ULTIMATE"}
        
        @{Name="Windows 8.1"; ImageFile="Win8"; ImageName="Windows 8.1"; CRLF=$true}
        @{Name="Windows 8.1 Pro"; ImageFile="Win8"; ImageName="Windows 8.1 Pro"}
        
        # The ISOs from the MediaCreationTool are apparently Technical Previews
        @{Name="Windows 10 Home"; ImageFile="Win10"; ImageName="Windows 10 Technical Preview"; CRLF=$true}
        @{Name="Windows 10 Pro"; ImageFile="Win10"; ImageName="Windows 10 Pro Technical Preview"}
    )
    
    # Build menu and get selection
    $dest_windows_version = $null
    $selection = $null
    $actions = @(@{Name="Main Menu"; Letter="M"})
    $selection = (menu-select "Which version of Windows are we installing?" $windows_versions $actions)
    
    if ($selection -imatch '^M$') {
        # User selected to return to the menu
        return $false
    } elseif ($selection -inotmatch '^\d+$') {
        # This shouldn't happen?
        throw
    } else {
        $selection -= 1
        $dest_windows_version = $windows_versions[$selection]
    }
    
    # Double check before deleting data
    wk-warn "SAFTEY CHECK:"
    wk-write ("  Installing:`t{0}" -f $dest_windows_version.Name)
    wk-error ("  And ERASING:`tDisk: {0}`t({1}) {2}`r`n" -f (human-size $dest_disk.Size 0), $dest_disk.PartitionStyle, $dest_disk.FriendlyName)
    if (!(ask "Is this correct?")) {
        wk-warn "Windows Setup aborted."
        wk-write ""
        pause "Press Enter to return to main menu... " -warning=$true
        return $false
    }
    
    ## WARNING
    wk-warn "WARNING: This section is experimental"
    ## WARNING
    
    ## Here be dragons
    try {
        # Select UEFI or BIOS partition layout
        if ($UEFI) {
            # System booted via UEFI so assume new layout should be GPT
            if (ask "Setup drive using GPT (UEFI) layout?") {
                format-gpt $dest_disk
            } else {
                format-mbr $dest_disk
            }
        } else{
            if (ask "Setup drive using MBR (legacy) layout?") {
                format-mbr $dest_disk
            } else {
                format-gpt $dest_disk
            }
        }
        
        # Apply image
        apply-image $dest_windows_version.ImageFile $dest_windows_version.ImageName
    
        # Create boot files (copies files for both Legacy and UEFI)
        wk-write "  Copying boot files..."
        bcdboot W:\Windows /s S: /f ALL 2>&1 | out-null
        if ($dest_windows_version.Name -imatch '^Windows (8|10)') {
            W:\Windows\System32\reagentc /setreimage /path T:\Recovery\WindowsRE /target W:\Windows 2>&1 | out-null
        }
        
        # Done
        wk-write "Windows Setup complete."
        wk-write ""
        pause "Press Enter to return to main menu... "
    } catch {
        # Error(s)
        wk-error "$Error"
        wk-error "Windows Setup aborted."
        wk-write ""
        pause "Press Enter to return to main menu... " -warning=$true
        return $false
    }
}
