# Wizard Kit: Windows PE Build Tool

## Init ##
#Requires -Version 3.0
#Requires -RunAsAdministrator
if (Test-Path Env:\DEBUG) {
    Set-PSDebug -Trace 1
}
$Host.UI.RawUI.WindowTitle = "Wizard Kit: Windows PE Build Tool"
$WD = $(Split-Path $MyInvocation.MyCommand.Path)
$Bin = (Get-Item $WD -Force).Parent.FullName
$Root = (Get-Item $Bin -Force).Parent.FullName
$Temp = "{0}\tmp" -f $Bin
$Date = Get-Date -UFormat "%Y-%m-%d"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
# $ProgressPreference = "silentlyContinue"
$SplitWindow = @()
$WinPEPackages = @(
    "WinPE-EnhancedStorage.cab",
    "en-us\WinPE-EnhancedStorage_en-us.cab",
    "WinPE-FMAPI.cab",
    "WinPE-WMI.cab",
    "en-us\WinPE-WMI_en-us.cab"
)
    # Install WinPE-WMI before you install WinPE-NetFX.
    # "WinPE-NetFx.cab",
    # "en-us\WinPE-NetFx_en-us.cab",

    # Install WinPE-WMI and WinPE-NetFX before you install WinPE-Scripting.
    # "WinPE-Scripting.cab",
    # "en-us\WinPE-Scripting_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, and WinPE-Scripting before you install WinPE-PowerShell.
    # "WinPE-PowerShell.cab",
    # "en-us\WinPE-PowerShell_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-DismCmdlets.
    # "WinPE-DismCmdlets.cab",
    # "en-us\WinPE-DismCmdlets_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
    # "WinPE-SecureBootCmdlets.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-StorageWMI.
    # "WinPE-StorageWMI.cab",
    # "en-us\WinPE-StorageWMI_en-us.cab",

## Fake DandISetEnv.bat ##
# $DVars = @(
    # @("DISMRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\DISM"),
    # @("BCDBootRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\BCDBoot"),
    # @("OSCDImgRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Oscdimg"),
    # @("WdsmcastRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\amd64\Wdsmcast"),
    # @("HelpIndexerRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\HelpIndexer"),
    # @("WSIMRoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Deployment Tools\WSIM"),
    # @("WinPERoot", "C:\Program Files (x86)\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment")
# )
# foreach ($d in $DVars) {
    # $varName = $d[0]
    # $varValue = $d[1]
    # Set-Item -Path Env:$varName -Value $varValue
    # Set-Item -Path Env:PATH -Value ($Env:PATH + ";$varValue")
# }
$DISM = "{0}\DISM.exe" -f $Env:DISMRoot

## Functions ##
function Ask-User ($text = "Kotaero") {
    $text += " [Y/N]"
    while ($true) {
        $answer = read-host $text
        if ($answer -imatch "^(y|yes)$") {
            $answer = $true
            break
        } elseif ($answer -imatch "^(n|no|nope)$") {
            $answer = $false
            break
        }
    }
    $answer
}
function Abort {
    Write-Host -ForegroundColor "Red" "`nAborted."
    WKPause "Press Enter to exit... "
    exit
}
function MakeClean {
    $Folders = @(
        "$Root\Mount",
        "$Root\PEFiles")
    $Clean = $false
    foreach ($f in $Folders) {
        if (Test-Path $f) {
            Write-Host -ForegroundColor "Yellow" ("Found: {0}" -f $f)
            $Clean = $true
        }
    }
    if (($Clean) -and (Ask-User "Delete the above folder(s)?")) {
        foreach ($f in $Folders) {
            if (Test-Path $f) {
                Remove-Item -Path $f -Recurse -Force
            }
        }
    }
}
function DownloadFile ($Path, $Name, $Url) {
    $OutFile = "{0}\{1}" -f $Path, $Name

    Write-Host ("Downloading: {0}" -f $Name)
    New-Item -Type Directory $Path 2>&1 | Out-Null
    try {
        Invoke-Webrequest -Uri $Url -OutFile $OutFile
    }
    catch {
        Write-Host ("  ERROR: Failed to download file." ) -ForegroundColor "Red"
    }
}
function FindDynamicUrl ($SourcePage, $RegEx) {
    $Url = ""

    # Get source page
    Invoke-Webrequest -Uri $SourcePage -OutFile "tmp_page"

    # Search for real url
    $Url = Get-Content "tmp_page" | Where-Object {$_ -imatch $RegEx}
    $Url = $Url -ireplace '.*(a |)href="([^"]+)".*', "$2"
    $Url = $Url -ireplace ".*(a |)href='([^']+)'.*", "$2"

    # Remove tmp_page
    Remove-Item "tmp_page"

    return $Url
}
function WKPause ($Message = "Press Enter to continue... ") {
    Write-Host $Message -NoNewLine
    Read-Host
}

## PowerShell equivalent of Python's "if __name__ == '__main__'"
# Code based on StackOverflow comments
# Question:     https://stackoverflow.com/q/4693947
# Using answer: https://stackoverflow.com/a/5582692
# Asked by:     https://stackoverflow.com/users/65164/mark-mascolino
# Answer by:    https://stackoverflow.com/users/696808/bacon-bits
if ($MyInvocation.InvocationName -ne ".") {
    # Clear-Host
    Write-Host "Wizard Kit: Windows PE Build Tool`n"
    
    ## Prep ##
    try {
        Import-Module -Name $Env:DISMRoot -ErrorAction "stop"
    }
    catch {
        Write-Host -ForegroundColor "Red" "ERROR: Failed to load DISM CmdLet"
        Abort
    }
    Push-Location "$WD"
    MakeClean
    
    ## Build ##
    foreach ($Arch in @("amd64", "x86")) {
        $Drivers = "$Root\Drivers\%arch"
        $Mount = "$Root\Mount"
        $PEFiles = "$Root\PEFiles\$arch"
        
        # Copy WinPE files
        Write-Host "Copying files..."
        $Cmd = ("{0}\copype.cmd" -f $Env:WinPERoot)
        Start-Process $Cmd -ArgumentList @($Arch, $PEFiles) -NoNewWindow -Wait
        
        # Remove unwanted items
        foreach ($SubDir in @("media", "media\Boot", "media\EFI\Microsoft\Boot")) {
            foreach ($Item in Get-ChildItem "$PEFiles\$SubDir") {
                if ($Item.Name -inotmatch "^(boot|efi|en-us|sources|fonts|resources|bcd|memtest)") {
                    Remove-Item -Path $Item.FullName -Recurse -Force
                }
            }
        }
        
        # Mount image
        Write-Host "Mounting image..."
        New-Item -Path $Mount -ItemType "directory" -Force | Out-Null
        Mount-WindowsImage -Path $Mount -ImagePath "$PEFiles\media\sources\boot.wim" -Index 1 | Out-Null
        
        # Add packages
        Write-Host "Adding packages:"
        foreach ($Package in $WinPEPackages) {
            $PackagePath = ("{0}\{1}\WinPE_OCs\{2}" -f $Env:WinPERoot, $Arch, $Package)
            Write-Host "    $Package..."
            Add-WindowsPackage –PackagePath $PackagePath –Path $Mount | Out-Null
        }
        
        # Set RamDisk size
        $ArgumentList = @(
            ('/Image:"{0}"' -f $Mount),
            "/Set-ScratchSpace:512"
        )
        Start-Process $DISM -ArgumentList $ArgumentList -NoNewWindow -Wait
        
        # Add WK tools
        Write-Host "Copying tools..."
        Copy-Item -Path "$Root\WK\$Arch" -Destination "$Mount\WK" -Recurse -Force
        Copy-Item -Path "$Root\WK\_include\*" -Destination "$Mount\WK" -Recurse -Force
        if ($Arch -eq "amd64") {
            $DestIni = "$Mount\WK\HWiNFO\HWiNFO64.INI"
        } else {
            $DestIni = "$Mount\WK\HWiNFO\HWiNFO32.INI"
        }
        Move-Item -Path "$Mount\WK\HWiNFO\HWiNFO.INI" -Destination $DestIni -Force
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\WK\ConEmu\ConEmu.jpg" -Recurse -Force
        Copy-Item -Path "$Root\Scripts" -Destination "$Mount\WK\Scripts" -Recurse -Force
        
        # Add System32 items
        Copy-Item -Path "$Root\System32\*" -Destination "$Mount\Windows\System32" -Recurse -Force
        $ArgumentList = @("/f", "$Mount\Windows\System32\winpe.jpg", "/a")
        Start-Process "C:\Windows\System32\takeown.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
        $ArgumentList = @("$Mount\Windows\System32\winpe.jpg", "/grant", "Administrators:F")
        Start-Process "C:\Windows\System32\icacls.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\Windows\System32\winpe.jpg" -Recurse -Force
        
        # Update registry
        Write-Host "Updating Registry..."
        $Reg = "C:\Windows\System32\reg.exe"
        Start-Process $Reg -ArgumentList @("load", "HKLM\WinPE-SW", "$Mount\Windows\System32\config\SOFTWARE") -NoNewWindow -Wait
        Start-Process $Reg -ArgumentList @("load", "HKLM\WinPE-SYS", "$Mount\Windows\System32\config\SYSTEM") -NoNewWindow -Wait
        
            # Add 7-Zip and Python to path
            $RegPath = "HKLM:\WinPE-SYS\ControlSet001\Control\Session Manager\Environment"
            $RegKey = Get-ItemProperty -Path $RegPath
            $NewValue = "{0};%SystemDrive%\WK\7-Zip;%SystemDrive%\WK\python;%SystemDrive%\WK\wimlib" -f $RegKey.Path
            Set-ItemProperty -Path $RegPath -Name "Path" -Value $NewValue -Force | Out-Null
            
            # Replace Notepad
            $RegPath = "HKLM:\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe"
            $NewValue = 'wscript "X:\WK\NotepadPlusPlus\npp.vbs"'
            New-Item -Path $RegPath -Force | Out-Null
            New-ItemProperty -Path $RegPath -Name "Debugger" -Value $NewValue -Force | Out-Null
        
        # Run garbage collection to release potential stale handles
        ## Credit: https://jrich523.wordpress.com/2012/03/06/powershell-loading-and-unloading-registry-hives/
        Start-Sleep -Seconds 2
        [gc]::collect()

        # Unload registry hives
        Start-Sleep -Seconds 2
        Start-Process $Reg -ArgumentList @("unload", "HKLM\WinPE-SW") -NoNewWindow -Wait
        Start-Process $Reg -ArgumentList @("unload", "HKLM\WinPE-SYS") -NoNewWindow -Wait
        
        # Unmount image
        Write-Host "Dismounting image..."
        Dismount-WindowsImage -Path $Mount -Save
        
        # Create ISO
        $ArgumentList = @("/iso", $PEFiles, "$Root\wk-winpe-$Date-$Arch.iso")
        $Cmd = "{0}\MakeWinPEMedia.cmd" -f $Env:WinPERoot
        Start-Process $Cmd -ArgumentList $ArgumentList -NoNewWindow -Wait
    }

    ## Done ##
    Pop-Location
    WKPause "Press Enter to exit... "
}
