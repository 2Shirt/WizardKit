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
$Temp = "$Bin\tmp"
$Date = Get-Date -UFormat "%Y-%m-%d"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
# $ProgressPreference = "silentlyContinue"
$HostSystem32 = "{0}\System32" -f $Env:SystemRoot
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

    Write-Host ("Downloading: $Name")
    New-Item -Type Directory $Path 2>&1 | Out-Null
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile
    }
    catch {
        Write-Host ("  ERROR: Failed to download file." ) -ForegroundColor "Red"
        $DownloadErrors += 1
    }
}
function FindDynamicUrl ($SourcePage, $RegEx) {
    # Get source page
    Invoke-Webrequest -Uri $SourcePage -OutFile "tmp_page"

    # Search for real url
    $Url = Get-Content "tmp_page" | Where-Object {$_ -imatch $RegEx}
    $Url = $Url -ireplace '.*(a |)href="([^"]+)".*', '$2'
    $Url = $Url -ireplace ".*(a |)href='([^']+)'.*", '$2'

    # Remove tmp_page
    Remove-Item "tmp_page"

    $Url | Select-Object -First 1
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
    Clear-Host
    Write-Host "Wizard Kit: Windows PE Build Tool`n`n`n`n`n"
    
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
    
    if (Ask-User "Update Tools?") {
        $DownloadErrors = 0
        
        ## Download Tools ##
        $ToolSources = @(
            # 7-Zip
            @("7z-installer.msi", "http://www.7-zip.org/a/7z1701.msi"),
            @("7z-extra.7z", "http://www.7-zip.org/a/7z1701-extra.7z"),
            # Blue Screen View
            @("bluescreenview64.zip", "http://www.nirsoft.net/utils/bluescreenview-x64.zip"),
            @("bluescreenview32.zip", "http://www.nirsoft.net/utils/bluescreenview.zip"),
            # ConEmu
            @("ConEmuPack.7z", "https://github.com/Maximus5/ConEmu/releases/download/v17.11.09/ConEmuPack.171109.7z"),
            # Fast Copy
            @("fastcopy64.zip", "http://ftp.vector.co.jp/69/28/2323/FastCopy332_x64.zip"),
            @("fastcopy32.zip", "http://ftp.vector.co.jp/69/28/2323/FastCopy332.zip"),
            # HWiNFO
            @("hwinfo64.zip", "http://app.oldfoss.com:81/download/HWiNFO/hw64_560.zip"),
            @("hwinfo32.zip", "http://app.oldfoss.com:81/download/HWiNFO/hw32_560.zip"),
            # Killer Network Drivers
            @(
                "killerinf.zip",
                ("http://www.killernetworking.com"+(FindDynamicUrl "http://www.killernetworking.com/driver-downloads/item/killer-drivers-inf" "Download Killer-Ethernet").replace('&amp;', '&'))
            ),
            # Notepad++
            @("npp_amd64.7z", "https://notepad-plus-plus.org/repository/7.x/7.5.2/npp.7.5.2.bin.minimalist.x64.7z"),
            @("npp_x86.7z", "https://notepad-plus-plus.org/repository/7.x/7.5.2/npp.7.5.2.bin.minimalist.7z"),
            # NT Password Editor
            @("ntpwed.zip", "http://cdslow.org.ru/files/ntpwedit/ntpwed07.zip"),
            # Prime95
            @("prime95_64.zip", "http://www.mersenne.org/ftp_root/gimps/p95v294b5.win64.zip"),
            @("prime95_32.zip", "http://www.mersenne.org/ftp_root/gimps/p95v294b5.win32.zip"),
            # ProduKey
            @("produkey64.zip", "http://www.nirsoft.net/utils/produkey-x64.zip"),
            @("produkey32.zip", "http://www.nirsoft.net/utils/produkey.zip"),
            # Python
            @("python64.zip", "https://www.python.org/ftp/python/3.6.3/python-3.6.3-embed-amd64.zip"),
            @("python32.zip", "https://www.python.org/ftp/python/3.6.3/python-3.6.3-embed-win32.zip"),
            # Python: psutil
            @(
                "psutil64.whl",
                (FindDynamicUrl "https://pypi.python.org/pypi/psutil" "href=.*-cp36-cp36m-win_amd64.whl")
            ),
            @(
                "psutil32.whl",
                (FindDynamicUrl "https://pypi.python.org/pypi/psutil" "href=.*-cp36-cp36m-win32.whl")
            ),
            # Q-Dir
            @("qdir64.zip", "https://www.softwareok.com/Download/Q-Dir_Portable_x64.zip"),
            @("qdir32.zip", "https://www.softwareok.com/Download/Q-Dir_Portable.zip"),
            # TestDisk / PhotoRec
            @("testdisk64.zip", "https://www.cgsecurity.org/testdisk-7.1-WIP.win64.zip"),
            @("testdisk32.zip", "https://www.cgsecurity.org/testdisk-7.1-WIP.win.zip"),
            # wimlib-imagex
            @("wimlib64.zip", "https://wimlib.net/downloads/wimlib-1.12.0-windows-x86_64-bin.zip"),
            @("wimlib32.zip", "https://wimlib.net/downloads/wimlib-1.12.0-windows-i686-bin.zip")
        )
        foreach ($Tool in $ToolSources) {
            DownloadFile -Path $Temp -Name $Tool[0] -Url $Tool[1]
        }
        
        ## Bail ##
        # If errors were encountered during downloads
        if ($DownloadErrors -gt 0) {
            Abort
        }
        
        ## Extract ##
        # 7-Zip
        Write-Host "Extracting: 7-Zip"
        try {
            $ArgumentList = @("/a", "$Temp\7z-installer.msi", "TARGETDIR=$Temp\7zi", "/qn")
            Start-Process -FilePath "$HostSystem32\msiexec.exe" -ArgumentList $ArgumentList -Wait
            $SevenZip = "$Temp\7zi\Files\7-Zip\7z.exe"
            $ArgumentList = @(
                "e", "$Temp\7z-extra.7z", "-o$Root\WK\amd64\7-Zip",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "x64\7za.exe", "*.txt")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "e", "$Temp\7z-extra.7z", "-o$Root\WK\x86\7-Zip",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "7za.exe", "*.txt")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\7z*" -Recurse
            $SevenZip = "$Root\WK\x86\7-Zip\7za.exe"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }

        # Blue Screen View
        Write-Host "Extracting: BlueScreenView"
        try {
            $ArgumentList = @(
                "x", "$Temp\bluescreenview64.zip", "-o$Root\WK\amd64\BlueScreenView",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\bluescreenview32.zip", "-o$Root\WK\x86\BlueScreenView",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\bluescreenview*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # ConEmu
        Write-Host "Extracting: ConEmu"
        try {
            $ArgumentList = @(
                "x", "$Temp\ConEmuPack.7z", "-o$Root\WK\amd64\ConEmu",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Root\WK\amd64\ConEmu\ConEmu.exe"
            Remove-Item "$Root\WK\amd64\ConEmu\ConEmu.map"
            Move-Item "$Root\WK\amd64\ConEmu\ConEmu64.exe" "$Root\WK\amd64\ConEmu\ConEmu.exe" -Force
            Move-Item "$Root\WK\amd64\ConEmu\ConEmu64.map" "$Root\WK\amd64\ConEmu\ConEmu.map" -Force
            $ArgumentList = @(
                "x", "$Temp\ConEmuPack.7z", "-o$Root\WK\x86\ConEmu",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Root\WK\x86\ConEmu\ConEmu64.exe"
            Remove-Item "$Root\WK\x86\ConEmu\ConEmu64.map"
            Remove-Item "$Temp\ConEmuPack*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }

        # Fast Copy
        Write-Host "Extracting: FastCopy"
        try {
            $ArgumentList = @(
                "x", "$Temp\fastcopy64.zip", "-o$Root\WK\amd64\FastCopy",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "-x!setup.exe", "-x!*.dll")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "e", "$Temp\fastcopy32.zip", "-o$Root\WK\x86\FastCopy",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "-x!setup.exe", "-x!*.dll")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\fastcopy*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # Killer Network Driver
        Write-Host "Extracting: Killer Network Driver"
        try {
            $ArgumentList = @(
                "e", "$Temp\killerinf.zip", "-o$Root\Drivers\amd64\Killer",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "Production\Windows10-x64\Eth\*")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "e", "$Temp\killerinf.zip", "-o$Root\Drivers\x86\Killer",
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "Production\Windows10-x86\Eth\*")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\killerinf*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # HWiNFO
        Write-Host "Extracting: HWiNFO"
        try {
            $ArgumentList = @(
                "e", "$Temp\hwinfo64.zip", "-o$Root\WK\amd64\HWiNFO",
                "-aoa", "-bso0", "-bse0", "-bsp0", "HWiNFO64.exe")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "e", "$Temp\hwinfo32.zip", "-o$Root\WK\x86\HWiNFO",
                "-aoa", "-bso0", "-bse0", "-bsp0", "HWiNFO32.exe")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\hwinfo*"
            Move-Item "$Root\WK\amd64\HWiNFO\HWiNFO64.exe" "$Root\WK\amd64\HWiNFO\HWiNFO.exe" -Force
            Move-Item "$Root\WK\x86\HWiNFO\HWiNFO32.exe" "$Root\WK\x86\HWiNFO\HWiNFO.exe" -Force
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # Notepad++
        Write-Host "Extracting: Notepad++"
        try {
            $ArgumentList = @(
                "x", "$Temp\npp_amd64.7z", "-o$Root\WK\amd64\NotepadPlusPlus",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\npp_x86.7z", "-o$Root\WK\x86\NotepadPlusPlus",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\npp*"
            Move-Item "$Root\WK\amd64\NotepadPlusPlus\notepad++.exe" "$Root\WK\amd64\NotepadPlusPlus\notepadplusplus.exe" -Force
            Move-Item "$Root\WK\x86\NotepadPlusPlus\notepad++.exe" "$Root\WK\x86\NotepadPlusPlus\notepadplusplus.exe" -Force
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }

        # NT Password Editor
        Write-Host "Extracting: NT Password Editor"
        try {
            $ArgumentList = @(
                "e", "$Temp\ntpwed.zip", ('-o"{0}\WK\amd64\NT Password Editor"' -f $Root),
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "ntpwedit64.exe", "*.txt")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Move-Item "$Root\WK\amd64\NT Password Editor\ntpwedit64.exe" "$Root\WK\amd64\NT Password Editor\ntpwedit.exe" -Force
            $ArgumentList = @(
                "e", "$Temp\ntpwed.zip", ('-o"{0}\WK\x86\NT Password Editor"' -f $Root),
                "-aoa", "-bso0", "-bse0", "-bsp0",
                "ntpwedit.exe", "*.txt")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\ntpwed*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # PhotoRec / TestDisk
        Write-Host "Extracting: PhotoRec / TestDisk"
        try {
            $ArgumentList = @(
                "x", "$Temp\testdisk64.zip", "-o$Root\WK\amd64\TestDisk",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            # Remove destination since Move-Item -Force can't handle this recursive merge
            Remove-Item "$Root\WK\amd64\TestDisk" -Recurse -Force
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Move-Item "$Root\WK\amd64\TestDisk\testdisk-7.1-WIP\*" "$Root\WK\amd64\TestDisk" -Force
            Remove-Item "$Root\WK\amd64\TestDisk\testdisk-7.1-WIP" -Recurse -Force
            $ArgumentList = @(
                "x", "$Temp\testdisk32.zip", "-o$Root\WK\x86\TestDisk",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            # Remove destination since Move-Item -Force can't handle this recursive merge
            Remove-Item "$Root\WK\x86\TestDisk" -Recurse -Force
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Move-Item "$Root\WK\x86\TestDisk\testdisk-7.1-WIP\*" "$Root\WK\x86\TestDisk" -Force
            Remove-Item "$Root\WK\x86\TestDisk\testdisk-7.1-WIP" -Recurse -Force
            Remove-Item "$Temp\testdisk*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # Prime95
        Write-Host "Extracting: Prime95"
        try {
            $ArgumentList = @(
                "x", "$Temp\prime95_64.zip", "-o$Root\WK\amd64\Prime95",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\prime95_32.zip", "-o$Root\WK\x86\Prime95",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\prime95*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # ProduKey
        try {
            $ArgumentList = @(
                "x", "$Temp\produkey64.zip", "-o$Root\WK\amd64\ProduKey",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\produkey32.zip", "-o$Root\WK\x86\ProduKey",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\produkey*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # Python (x64)
        Write-Host "Extracting: Python (x64)"
        try {
            $ArgumentList = @(
                "x", "$Temp\python64.zip", "-o$Root\WK\amd64\python",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\psutil64.whl", "-o$Root\WK\amd64\python",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }

        # Python (x32)
        Write-Host "Extracting: Python (x32)"
        try {
            $ArgumentList = @(
                "x", "$Temp\python32.zip", "-o$Root\WK\x86\python",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\psutil32.whl", "-o$Root\WK\x86\python",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        Remove-Item "$Temp\python*"
        Remove-Item "$Temp\*.whl"
    
        # Q-Dir
        Write-Host "Extracting: Q-Dir"
        try {
            $ArgumentList = @(
                "x", "$Temp\qdir64.zip", "-o$Root\WK\amd64",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\qdir32.zip", "-o$Root\WK\x86",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\qdir*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
        
        # wimlib-imagex
        try {
            $ArgumentList = @(
                "x", "$Temp\wimlib64.zip", "-o$Root\WK\amd64\wimlib",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            $ArgumentList = @(
                "x", "$Temp\wimlib32.zip", "-o$Root\WK\x86\wimlib",
                "-aoa", "-bso0", "-bse0", "-bsp0")
            Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
            Remove-Item "$Temp\wimlib*"
        }
        catch {
            Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
        }
    }
    
    ## Build ##
    foreach ($Arch in @("amd64", "x86")) {
        $Drivers = "$Root\Drivers\$Arch"
        $Mount = "$Root\Mount"
        $PEFiles = "$Root\PEFiles\$Arch"
        
        # Copy WinPE files
        Write-Host "Copying files..."
        $Cmd = ("{0}\copype.cmd" -f $Env:WinPERoot)
        Start-Process -FilePath $Cmd -ArgumentList @($Arch, $PEFiles) -NoNewWindow -Wait
        
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
        
        # Add drivers
        Add-WindowsDriver -Path $Mount -Driver $Drivers -Recurse | Out-Null
        
        # Add packages
        Write-Host "Adding packages:"
        $WinPEPackages = @(
            "WinPE-EnhancedStorage",
            "WinPE-FMAPI",
            "WinPE-WMI",
            "WinPE-SecureStartup"
        )
        foreach ($Package in $WinPEPackages) {
            $PackagePath = ("{0}\{1}\WinPE_OCs\{2}.cab" -f $Env:WinPERoot, $Arch, $Package)
            Write-Host "    $Package..."
            Add-WindowsPackage –PackagePath $PackagePath –Path $Mount | Out-Null
            $LangPackagePath = ("{0}\{1}\WinPE_OCs\en-us\{2}_en-us.cab" -f $Env:WinPERoot, $Arch, $Package)
            if (Test-Path $LangPackagePath) {
                Add-WindowsPackage –PackagePath $LangPackagePath –Path $Mount | Out-Null
            }
        }
        
        # Set RamDisk size
        $ArgumentList = @(
            ('/Image:"{0}"' -f $Mount),
            "/Set-ScratchSpace:512"
        )
        Start-Process -FilePath $DISM -ArgumentList $ArgumentList -NoNewWindow -Wait
        
        # Add tools
        Write-Host "Copying tools..."
        Copy-Item -Path "$Root\WK\$Arch" -Destination "$Mount\.bin" -Recurse -Force
        Copy-Item -Path "$Root\WK\_include\*" -Destination "$Mount\.bin" -Recurse -Force
        if ($Arch -eq "amd64") {
            $DestIni = "$Mount\.bin\HWiNFO\HWiNFO64.INI"
        } else {
            $DestIni = "$Mount\.bin\HWiNFO\HWiNFO32.INI"
        }
        Move-Item -Path "$Mount\.bin\HWiNFO\HWiNFO.INI" -Destination $DestIni -Force
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\.bin\ConEmu\ConEmu.jpg" -Recurse -Force
        Copy-Item -Path "$Root\Scripts" -Destination "$Mount\.bin\Scripts" -Recurse -Force
        
        # Add System32 items
        $HostSystem32 = "{0}\System32" -f $Env:SystemRoot
        Copy-Item -Path "$Root\System32\*" -Destination "$Mount\Windows\System32" -Recurse -Force
        $ArgumentList = @("/f", "$Mount\Windows\System32\winpe.jpg", "/a")
        Start-Process -FilePath "$HostSystem32\takeown.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
        $ArgumentList = @("$Mount\Windows\System32\winpe.jpg", "/grant", "Administrators:F")
        Start-Process -FilePath "$HostSystem32\icacls.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
        Copy-Item -Path "$Root\WinPE.jpg" -Destination "$Mount\Windows\System32\winpe.jpg" -Recurse -Force
        
        # Load registry hives
        Write-Host "Updating Registry..."
        $Reg = "$HostSystem32\reg.exe"
        $ArgumentList = @("load", "HKLM\WinPE-SW", "$Mount\Windows\System32\config\SOFTWARE")
        Start-Process -FilePath $Reg -ArgumentList $ArgumentList -NoNewWindow -Wait
        $ArgumentList = @("load", "HKLM\WinPE-SYS", "$Mount\Windows\System32\config\SYSTEM")
        Start-Process -FilePath $Reg -ArgumentList $ArgumentList -NoNewWindow -Wait
        
        # Add tools to path
        ## .NET code to properly handle REG_EXPAND_SZ values
        ## Credit: https://www.sepago.com/blog/2013/08/22/reading-and-writing-regexpandsz-data-with-powershell
        ## By: Marius Gawenda
        $Hive = [Microsoft.Win32.Registry]::LocalMachine
        $RegPath = "WinPE-SYS\ControlSet001\Control\Session Manager\Environment"
        $RegKey = $Hive.OpenSubKey($RegPath)
        $CurValue = $RegKey.GetValue(
            "Path", $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $NewValue = "$CurValue;%SystemDrive%\.bin\7-Zip;%SystemDrive%\.bin\python;%SystemDrive%\.bin\wimlib"
        Set-ItemProperty -Path "HKLM:\$RegPath" -Name "Path" -Value $NewValue -Force | Out-Null
        $Hive.close()
        $RegKey.close()
        
        # Replace Notepad
        $RegPath = "HKLM:\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe"
        $NewValue = 'cmd /c "%SystemDrive%\.bin\NotepadPlusPlus\npp.cmd"'
        New-Item -Path $RegPath -Force | Out-Null
        New-ItemProperty -Path $RegPath -Name "Debugger" -Value $NewValue -Force | Out-Null
        
        # Run garbage collection to release potential stale handles
        ## Credit: https://jrich523.wordpress.com/2012/03/06/powershell-loading-and-unloading-registry-hives/
        Start-Sleep -Seconds 2
        [gc]::collect()

        # Unload registry hives
        Start-Sleep -Seconds 2
        Start-Process -FilePath $Reg -ArgumentList @("unload", "HKLM\WinPE-SW") -NoNewWindow -Wait
        Start-Process -FilePath $Reg -ArgumentList @("unload", "HKLM\WinPE-SYS") -NoNewWindow -Wait
        
        # Unmount image
        Write-Host "Dismounting image..."
        Dismount-WindowsImage -Path $Mount -Save
        
        # Create ISO
        $ArgumentList = @("/iso", $PEFiles, "$Root\wk-winpe-$Date-$Arch.iso")
        $Cmd = "{0}\MakeWinPEMedia.cmd" -f $Env:WinPERoot
        Start-Process -FilePath $Cmd -ArgumentList $ArgumentList -NoNewWindow -Wait
    }

    ## Done ##
    Pop-Location
    Write-Host "`nDone."
    WKPause "Press Enter to exit... "
}
