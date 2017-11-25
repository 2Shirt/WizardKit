# WK-Checklist

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
. .\servers.ps1
. .\imaging.ps1
clear
$host.UI.RawUI.WindowTitle = "WK PE Tool"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | Out-Null
$log = "$logpath\winpe.log"

# Functions
function wk-exit {
    param([string]$action)
    switch ($action) {
        'Q' {PowerShell -ExecutionPolicy Bypass; break}
        'R' {wpeutil reboot; break}
        'S' {wpeutil shutdown; break}
        default {throw}
    }
    exit 0
}
function menu-tools {
    # Avail tools
    $tools = @(
        @{Name="Blue Screen View"; Folder="BlueScreenView"; File="BlueScreenView.exe"},
        @{Name="CPU-Z"; Folder="CPU-Z"; File="cpuz.exe"},
        @{Name="Explorer++"; Folder="Explorer++"; File="Explorer++.exe"},
        @{Name="Fast Copy"; Folder="FastCopy"; File="FastCopy.exe"; Args=@('/cmd=noexist_only', '/utf8', '/skip_empty_dir', '/linkdest', '/exclude="desktop.ini;Thumbs.db"')},
        @{Name="HW Monitor"; Folder="HWMonitor"; File="HWMonitor.exe"},
        @{Name="NT Password Editor"; Folder="NT Password Editor"; File="ntpwedit.exe"},
        @{Name="Notepad2"; Folder="Notepad2"; File="Notepad2-Mod.exe"},
        @{Name="PhotoRec"; Folder="TestDisk"; File="photorec_win.exe"},
        @{Name="Prime95"; Folder="Prime95"; File="prime95.exe"},
        @{Name="ProduKey"; Folder="ProduKey"; File="ProduKey.exe"},
        @{Name="TestDisk"; Folder="TestDisk"; File="testdisk_win.exe"}
    )
    
    # Build menu
    $selection = $null
    $actions = @(@{Name="Main Menu"; Letter="M"})
    
    # Run Loop
    $_done = $false
    do {
        $selection = (menu-select "Tools Menu" $tools $actions)
        
        if ($selection -imatch '^M$') {
            # User selected to return to the menu
            return $false
        } elseif ($selection -inotmatch '^\d+$') {
            # This shouldn't happen?
            throw
        } else {
            $selection -= 1
            $path = "{0}\{1}" -f $WKPath, $tools[$selection].Folder
            if ($tools[$selection].ContainsKey("Args")) {
                Start-Process $tools[$selection].File -ArgumentList $tools[$selection].Args -WorkingDirectory $path
            } else {
                Start-Process $tools[$selection].File -WorkingDirectory $path
            }
        }
    } until ($_done)
}
function menu-main {
    # Build menu
    $selection = $null
    $menus = @(
        @{Name="Drive Imaging"; Menu="menu-imaging"}
        @{Name="Windows Setup"; Menu="menu-setup"}
        @{Name="Misc Tools"; Menu="menu-tools"}
    )
    $actions = @(
        @{Name="Command Prompt"; Letter="C"}
        @{Name="PowerShell"; Letter="P"}
        @{Name="Reboot"; Letter="R"}
        @{Name="Shutdown"; Letter="S"}
    )
    
    # Show Menu
    $selection = (menu-select "Main Menu" $menus $actions -SecretExit $true)
    
    if ($selection -imatch '^C$') {
        Start-Process "$windir\System32\cmd.exe" -argumentlist @("-new_console:n") -WorkingDirectory "$WKPath"
        return
    } elseif ($selection -imatch '^P$') {
        Start-Process "$windir\System32\WindowsPowerShell\v1.0\powershell.exe" -argumentlist @("-ExecutionPolicy", "Bypass", "-NoProfile", "-new_console:n") -WorkingDirectory "$WKPath"
        return
    } elseif ($selection -imatch '^[QRS]$') {
        wk-exit $selection
        return
    } elseif ($selection -inotmatch '^\d+$') {
        # This shouldn't happen?
        throw
    } else {
        # Launch sub-menu
        $selection -= 1
        & $menus[$selection].Menu
    }
}

# Mount all partitions
foreach ($_d in @(Get-Disk)) {
    foreach ($_p in @(Get-Partition -DiskNumber $_d.DiskNumber)) {
        # Assign letter
        Add-PartitionAccessPath -DiskNumber $_d.DiskNumber -PartitionNumber $_p.PartitionNumber -AssignDriveLetter 2>&1 | Out-Null
    }
}

# Main Loop
do {
    menu-main
} while ($true)
