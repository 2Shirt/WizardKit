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
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
$ProgressPreference = "silentlyContinue"
$SplitWindow = @()
$DISM = "{0}\DISM.exe" -f $Env:DISMRoot
$WinPEPackages = @(
    "WinPE-EnhancedStorage.cab",
    "WinPE-FMAPI.cab",
    "WinPE-WMI.cab",
    "WinPE-EnhancedStorage_en-us.cab",
    "WinPE-WMI_en-us.cab"
)
    # Install WinPE-WMI before you install WinPE-NetFX.
    # "WinPE-NetFx.cab",
    # "WinPE-NetFx_en-us.cab",

    # Install WinPE-WMI and WinPE-NetFX before you install WinPE-Scripting.
    # "WinPE-Scripting.cab",
    # "WinPE-Scripting_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, and WinPE-Scripting before you install WinPE-PowerShell.
    # "WinPE-PowerShell.cab",
    # "WinPE-PowerShell_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-DismCmdlets.
    # "WinPE-DismCmdlets.cab",
    # "WinPE-DismCmdlets_en-us.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
    # "WinPE-SecureBootCmdlets.cab",

    # Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-StorageWMI.
    # "WinPE-StorageWMI.cab",
    # "WinPE-StorageWMI_en-us.cab",

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
function WKRun ($Cmd, $ArgumentList) {
    Start-Process $Cmd -ArgumentList $ArgumentList -NoNewWindow -Wait
    # Write-Host ("Cmd: == {0} ==" -f $Cmd)
    # Write-Host ("ArgumentList:")
    # foreach ($a in $ArgumentList) {
        # Write-Host ("`t == {0} ==" -f $a)
    # }
    # Write-Host ("Check: == {0} ==" -f $Check)
    # Write-Host ("SplitWindow: == {0} ==" -f $SplitWindow)
}

## PowerShell equivalent of Python's "if __name__ == '__main__'"
# Code based on StackOverflow comments
# Question:     https://stackoverflow.com/q/4693947
# Using answer: https://stackoverflow.com/a/5582692
# Asked by:     https://stackoverflow.com/users/65164/mark-mascolino
# Answer by:    https://stackoverflow.com/users/696808/bacon-bits
if ($MyInvocation.InvocationName -ne ".") {
    Clear-Host
    Write-Host "Wizard Kit: Windows PE Build Tool`n"
    
    ## Prep ##
    Push-Location "$WD"
    $Date = Get-Date -UFormat "%Y-%m-%d"
    MakeClean
    
    ## Build ##
    foreach ($Arch in @("amd64", "x86")) {
        $Drivers = "$Root\Drivers\%arch"
        $Mount = "$Root\Mount"
        $PEFiles = "$Root\PEFiles\$arch"
        
        # Copy WinPE files
        Write-Host "Copying files..."
        $Cmd = ("{0}\copype.cmd" -f $Env:WinPERoot)
        WKRun -Cmd $Cmd -ArgumentList @($Arch, $PEFiles)
        
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
        $ArgumentList = @(
            "/Mount-Image",
            ('/ImageFile:"{0}\media\sources\boot.wim"' -f $PEFiles),
            "/Index:1",
            ('/MountDir:"{0}"' -f $Mount)
        )
        WKRun -Cmd $DISM -ArgumentList $ArgumentList
        
        # Add packages
        Write-Host "Adding packages..."
        foreach ($Package in $WinPEPackages) {
            $PackagePath = "{0}\{1}\WinPE_OCs" -f $Env:WinPERoot, $Arch
            $ArgumentList = @(
                "/Add-Package",
                ('/Image:"{0}"' -f $Mount),
                ('/PackagePath:"{0}"' -f $PackagePath)
            )
            WKRun -Cmd $DISM -ArgumentList $ArgumentList
        }
        
        # Set RamDisk size
        $ArgumentList = @(
            ('/Image:"{0}"' -f $Mount),
            "/Set-ScratchSpace:512"
        )
        WKRun -Cmd $DISM -ArgumentList $ArgumentList
        
        # Add WK tools
        Write-Host "Copying tools..."
        Copy-Item -Path "$Root\WK\$Arch" -Destination "$Mount\WK" -Recurse -Force
        Copy-Item -Path "$Root\WK\_include\*" -Destination "$Mount\WK" -Recurse -Force
        if ($Arch -eq "amd64") {
            $DestIni = "$Mount\WK\HWiNFO\HWiNFO64.INI"
        } else {
            $DestIni = "$Mount\WK\HWiNFO\HWiNFO32.INI"
        }
        Move-Item -Path "$Root\WK\HWiNFO\HWiNFO.INI" -Destination $DestIni -Force
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\WK\ConEmu\ConEmu.jpg" -Recurse -Force
        Copy-Item -Path "$Root\Scripts" -Destination "$Mount\WK\Scripts" -Recurse -Force
        
        # Add System32 items
        Copy-Item -Path "$Root\System32" -Destination "$Mount\Windows\System32" -Recurse -Force
        $ArgumentList = @("/f", "$Mount\Windows\System32\winpe.jpg", "/a")
        WKRun -Cmd "C:\Windows\System32\takeown.exe" -ArgumentList $ArgumentList
        $ArgumentList = @("$Mount\Windows\System32\winpe.jpg", "/grant", "Administrators:F")
        WKRun -Cmd "C:\Windows\System32\icacls.exe" -ArgumentList $ArgumentList
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\Windows\System32\winpe.jpg" -Recurse -Force
        
        # Update registry
        Write-Host "Updating Registry..."
        $Reg = "C:\Windows\System32\reg.exe"
        WKRun -Cmd $Reg -ArgumentList @("load", "HKLM\WinPE-SW", "$Mount\Windows\System32\config\SOFTWARE")
        WKRun -Cmd $Reg -ArgumentList @("load", "HKLM\WinPE-SYS", "$Mount\Windows\System32\config\SYSTEM")
        
            # Add 7-Zip and Python to path
            $RegPath = "HKLM:\WinPE-SYS\ControlSet001\Control\Session Manager\Environment"
            $RegKey = Get-ItemProperty -Path $RegPath
            $NewValue = "{0};%SystemDrive%\WK\7-Zip;%SystemDrive%\WK\python;%SystemDrive%\WK\wimlib" -f $RegKey.Path
            Set-ItemProperty -Path $RegPath -Name "Path" -Value $NewValue -Force
            
            # Replace Notepad
            $RegPath = "HKLM:\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe"
            $NewValue = 'wscript "X:\WK\NotepadPlusPlus\npp.vbs"'
            New-Item -Path $RegPath -Force
            New-ItemProperty -Path $RegPath -Name "Debugger" -Value $NewValue -Force

        # Unload registry hives
        Start-Sleep -Seconds 1
        WKRun -Cmd $Reg -ArgumentList @("unload", "HKLM\WinPE-SW")
        WKRun -Cmd $Reg -ArgumentList @("unload", "HKLM\WinPE-SYS")
        
        # Unmount image
        Write-Host "Dismounting image..."
        $ArgumentList = @(
            "/Unmount-Image",
            ('/MountDir:"{0}"' -f $Mount),
            "/Commit")
        WKRun -Cmd $DISM -ArgumentList $ArgumentList
        
        # Create ISO
        $ArgumentList = @("/iso", $PEFiles, "wk-winpe-$Date-$Arch.iso")
        $Cmd = "{0}\MakeWinPEMedia.cmd" -f $Env:WinPERoot
        WKRun -Cmd $Cmd -ArgumentList $ArgumentList
    }

    ## Done ##
    Pop-Location
}
