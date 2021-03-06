﻿# Wizard Kit: Windows PE Build Tool

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
$Build = "$Root\BUILD_PE"
$LogDir = "$Build\Logs"
$Temp = "$Build\Temp"
$Date = Get-Date -UFormat "%Y-%m-%d"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
$HostSystem32 = "{0}\System32" -f $Env:SystemRoot
$HostSysWOW64 = "{0}\SysWOW64" -f $Env:SystemRoot
$DISM = "{0}\DISM.exe" -f $Env:DISMRoot
#Enable TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

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
    "$Build\Mount",
    "$Build\PEFiles")
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
    $global:DownloadErrors += 1
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
  New-Item -Type Directory $Build 2>&1 | Out-Null
  New-Item -Type Directory $LogDir 2>&1 | Out-Null

  ## main.py ##
  if (!(Test-Path "$Build\main.py") -or (Ask-User "Replace existing main.py?")) {
    Copy-Item -Path "$Bin\Scripts\settings\main.py" -Destination "$Build\main.py" -Force
  }
  WKPause "Press Enter to open settings..."
  Start-Process "$HostSystem32\notepad.exe" -ArgumentList @("$Build\main.py") -Wait
  $KitNameFull = (Get-Content "$Build\main.py" | Where-Object {$_ -match 'FULL'}) -replace ".*'(.*)'$", '$1'
  $KitNameShort = (Get-Content "$Build\main.py" | Where-Object {$_ -match 'SHORT'}) -replace ".*'(.*)'$", '$1'

  if (Ask-User "Update Tools?") {
    $DownloadErrors = 0

    ## Download Tools ##
    $ToolSources = @(
      # 7-Zip
      @("7z-installer.msi", "https://www.7-zip.org/a/7z1900.msi"),
      @("7z-extra.7z", "https://www.7-zip.org/a/7z1900-extra.7z"),
      # Blue Screen View
      @("bluescreenview32.zip", "http://www.nirsoft.net/utils/bluescreenview.zip"),
      @("bluescreenview64.zip", "http://www.nirsoft.net/utils/bluescreenview-x64.zip"),
      # ConEmu
      @("ConEmuPack.7z", "https://github.com/Maximus5/ConEmu/releases/download/v19.03.10/ConEmuPack.190310.7z"),
      # Fast Copy
      @("fastcopy.zip", "http://ftp.vector.co.jp/71/31/2323/FastCopy363_installer.exe"),
      # HWiNFO
      @("hwinfo.zip", "http://files2.majorgeeks.com/377527622c5325acc1cb937fb149d0de922320c0/systeminfo/hwi_602.zip"),
      # Killer Network Drivers
      @(
        "killerinf.zip",
        ("https://www.killernetworking.com"+(FindDynamicUrl "https://www.killernetworking.com/killersupport/category/other-downloads" "Download Killer-Ethernet").replace('&amp;', '&'))
      ),
      # Notepad++
      @("npp_x86.7z", "https://notepad-plus-plus.org/repository/7.x/7.6.4/npp.7.6.4.bin.minimalist.7z"),
      @("npp_amd64.7z", "https://notepad-plus-plus.org/repository/7.x/7.6.4/npp.7.6.4.bin.minimalist.x64.7z"),
      # NT Password Editor
      @("ntpwed.zip", "http://cdslow.org.ru/files/ntpwedit/ntpwed07.zip"),
      # Prime95
      @("prime95_32.zip", "http://www.mersenne.org/ftp_root/gimps/p95v294b7.win32.zip"),
      @("prime95_64.zip", "http://www.mersenne.org/ftp_root/gimps/p95v294b8.win64.zip"),
      # ProduKey
      @("produkey32.zip", "http://www.nirsoft.net/utils/produkey.zip"),
      @("produkey64.zip", "http://www.nirsoft.net/utils/produkey-x64.zip"),
      # Python
      @("python32.zip", "https://www.python.org/ftp/python/3.7.2/python-3.7.2.post1-embed-win32.zip"),
      @("python64.zip", "https://www.python.org/ftp/python/3.7.2/python-3.7.2.post1-embed-amd64.zip"),
      # Python: psutil
      @(
        "psutil64.whl",
        (FindDynamicUrl "https://pypi.org/project/psutil/" "href=.*-cp37-cp37m-win_amd64.whl")
      ),
      @(
        "psutil32.whl",
        (FindDynamicUrl "https://pypi.org/project/psutil/" "href=.*-cp37-cp37m-win32.whl")
      ),
      # Q-Dir
      @("qdir32.zip", "https://www.softwareok.com/Download/Q-Dir_Portable.zip"),
      @("qdir64.zip", "https://www.softwareok.com/Download/Q-Dir_Portable_x64.zip"),
      # TestDisk / PhotoRec
      @("testdisk32.zip", "https://www.cgsecurity.org/testdisk-7.1-WIP.win.zip"),
      @("testdisk64.zip", "https://www.cgsecurity.org/testdisk-7.1-WIP.win64.zip"),
      # VirtIO drivers
      @("virtio-win.iso", "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/virtio-win.iso"),
      # Visual C++ Runtimes
      @("vcredist_x86.exe", "https://aka.ms/vs/15/release/vc_redist.x86.exe"),
      @("vcredist_x64.exe", "https://aka.ms/vs/15/release/vc_redist.x64.exe"),
      # wimlib-imagex
      @("wimlib32.zip", "https://wimlib.net/downloads/wimlib-1.13.0-windows-i686-bin.zip"),
      @("wimlib64.zip", "https://wimlib.net/downloads/wimlib-1.13.0-windows-x86_64-bin.zip")
    )
    foreach ($Tool in $ToolSources) {
      DownloadFile -Path $Temp -Name $Tool[0] -Url $Tool[1]
    }

    ## Bail ##
    # If errors were encountered during downloads
    if ($DownloadErrors -gt 0) {
      Abort
    }

    ## Install ##
    # Visual C++ Runtimes
    Write-Host "Installing: Visual C++ Runtimes"
    $ArgumentList = @("/install", "/passive", "/norestart")
    Start-Process -FilePath "$Temp\vcredist_x86.exe" -ArgumentList $ArgumentList -Wait
    Start-Process -FilePath "$Temp\vcredist_x64.exe" -ArgumentList $ArgumentList -Wait

    ## Extract ##
    # 7-Zip
    Write-Host "Extracting: 7-Zip"
    try {
      $ArgumentList = @("/a", "$Temp\7z-installer.msi", "TARGETDIR=$Temp\7zi", "/qn")
      Start-Process -FilePath "$HostSystem32\msiexec.exe" -ArgumentList $ArgumentList -Wait
      $SevenZip = "$Temp\7zi\Files\7-Zip\7z.exe"
      $ArgumentList = @(
        "e", "$Temp\7z-extra.7z", "-o$Build\bin\amd64\7-Zip",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "x64\7za.exe", "*.txt")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "e", "$Temp\7z-extra.7z", "-o$Build\bin\x86\7-Zip",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "7za.exe", "*.txt")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # Blue Screen View
    Write-Host "Extracting: BlueScreenView"
    try {
      $ArgumentList = @(
        "x", "$Temp\bluescreenview64.zip", "-o$Build\bin\amd64\BlueScreenView",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\bluescreenview32.zip", "-o$Build\bin\x86\BlueScreenView",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # ConEmu
    Write-Host "Extracting: ConEmu"
    try {
      $ArgumentList = @(
        "x", "$Temp\ConEmuPack.7z", "-o$Build\bin\amd64\ConEmu",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Remove-Item "$Build\bin\amd64\ConEmu\ConEmu.exe"
      Remove-Item "$Build\bin\amd64\ConEmu\ConEmu.map"
      Move-Item "$Build\bin\amd64\ConEmu\ConEmu64.exe" "$Build\bin\amd64\ConEmu\ConEmu.exe" -Force
      Move-Item "$Build\bin\amd64\ConEmu\ConEmu64.map" "$Build\bin\amd64\ConEmu\ConEmu.map" -Force
      $ArgumentList = @(
        "x", "$Temp\ConEmuPack.7z", "-o$Build\bin\x86\ConEmu",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Remove-Item "$Build\bin\x86\ConEmu\ConEmu64.exe"
      Remove-Item "$Build\bin\x86\ConEmu\ConEmu64.map"
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # Fast Copy
    Write-Host "Extracting: FastCopy"
    try {
      # Extract Installer
      $ArgumentList = @(
        "e", "$Temp\fastcopy.zip", "-o$Temp",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait

      # Extract 64-bit
      $ArgumentList = @(
        "/NOSUBDIR", "/DIR=$Build\bin\amd64\FastCopy",
        "/EXTRACT64")
      Start-Process -FilePath "$TEMP\FastCopy354_installer.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
      Remove-Item "$Build\bin\amd64\FastCopy\setup.exe" -Force

      # Extract 32-bit
      $ArgumentList = @(
        "/NOSUBDIR", "/DIR=$Build\bin\x86\FastCopy",
        "/EXTRACT32")
      Start-Process -FilePath "$TEMP\FastCopy354_installer.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
      Remove-Item "$Build\bin\x86\FastCopy\setup.exe" -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }


    # Killer Network Driver
    Write-Host "Extracting: Killer Network Driver"
    try {
      $ArgumentList = @(
        "e", "$Temp\killerinf.zip", "-o$Build\Drivers\amd64\Killer",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "Production\Windows10-x64\Eth\*")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "e", "$Temp\killerinf.zip", "-o$Build\Drivers\x86\Killer",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "Production\Windows10-x86\Eth\*")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # HWiNFO
    Write-Host "Extracting: HWiNFO"
    try {
      $ArgumentList = @(
        "e", "$Temp\hwinfo.zip", "-o$Build\bin\amd64\HWiNFO",
        "-aoa", "-bso0", "-bse0", "-bsp0", "HWiNFO64.exe")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "e", "$Temp\hwinfo.zip", "-o$Build\bin\x86\HWiNFO",
        "-aoa", "-bso0", "-bse0", "-bsp0", "HWiNFO32.exe")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\amd64\HWiNFO\HWiNFO64.exe" "$Build\bin\amd64\HWiNFO\HWiNFO.exe" -Force
      Move-Item "$Build\bin\x86\HWiNFO\HWiNFO32.exe" "$Build\bin\x86\HWiNFO\HWiNFO.exe" -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # Notepad++
    Write-Host "Extracting: Notepad++"
    try {
      $ArgumentList = @(
        "x", "$Temp\npp_amd64.7z", "-o$Build\bin\amd64\NotepadPlusPlus",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\npp_x86.7z", "-o$Build\bin\x86\NotepadPlusPlus",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\amd64\NotepadPlusPlus\notepad++.exe" "$Build\bin\amd64\NotepadPlusPlus\notepadplusplus.exe" -Force
      Move-Item "$Build\bin\x86\NotepadPlusPlus\notepad++.exe" "$Build\bin\x86\NotepadPlusPlus\notepadplusplus.exe" -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # NT Password Editor
    Write-Host "Extracting: NT Password Editor"
    try {
      $ArgumentList = @(
        "e", "$Temp\ntpwed.zip", ('-o"{0}\bin\amd64\NT Password Editor"' -f $Build),
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "ntpwedit64.exe", "*.txt")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\amd64\NT Password Editor\ntpwedit64.exe" "$Build\bin\amd64\NT Password Editor\ntpwedit.exe" -Force
      $ArgumentList = @(
        "e", "$Temp\ntpwed.zip", ('-o"{0}\bin\x86\NT Password Editor"' -f $Build),
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "ntpwedit.exe", "*.txt")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # PhotoRec / TestDisk
    Write-Host "Extracting: PhotoRec / TestDisk"
    try {
      $ArgumentList = @(
        "x", "$Temp\testdisk64.zip", "-o$Build\bin\amd64\TestDisk",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      # Remove destination since Move-Item -Force can't handle this recursive merge
      Remove-Item "$Build\bin\amd64\TestDisk" -Recurse -Force 2>&1 | Out-Null
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\amd64\TestDisk\testdisk-7.1-WIP\*" "$Build\bin\amd64\TestDisk" -Force
      Remove-Item "$Build\bin\amd64\TestDisk\testdisk-7.1-WIP" -Recurse -Force
      $ArgumentList = @(
        "x", "$Temp\testdisk32.zip", "-o$Build\bin\x86\TestDisk",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      # Remove destination since Move-Item -Force can't handle this recursive merge
      Remove-Item "$Build\bin\x86\TestDisk" -Recurse -Force 2>&1 | Out-Null
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\x86\TestDisk\testdisk-7.1-WIP\*" "$Build\bin\x86\TestDisk" -Force
      Remove-Item "$Build\bin\x86\TestDisk\testdisk-7.1-WIP" -Recurse -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # Prime95
    Write-Host "Extracting: Prime95"
    try {
      $ArgumentList = @(
        "x", "$Temp\prime95_64.zip", "-o$Build\bin\amd64\Prime95",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\prime95_32.zip", "-o$Build\bin\x86\Prime95",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # ProduKey
    try {
      $ArgumentList = @(
        "x", "$Temp\produkey64.zip", "-o$Build\bin\amd64\ProduKey",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\produkey32.zip", "-o$Build\bin\x86\ProduKey",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # Python (x64)
    Write-Host "Extracting: Python (x64)"
    try {
      $ArgumentList = @(
        "x", "$Temp\python64.zip", "-o$Build\bin\amd64\python",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\psutil64.whl", "-o$Build\bin\amd64\python",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait

    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }
    try {
      Copy-Item -Path "$HostSystem32\vcruntime140.dll" -Destination "$Build\bin\amd64\python\vcruntime140.dll" -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to copy Visual C++ Runtime DLL." ) -ForegroundColor "Red"
    }

    # Python (x32)
    Write-Host "Extracting: Python (x32)"
    try {
      $ArgumentList = @(
        "x", "$Temp\python32.zip", "-o$Build\bin\x86\python",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\psutil32.whl", "-o$Build\bin\x86\python",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait

    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }
    try {
      Copy-Item -Path "$HostSysWOW64\vcruntime140.dll" -Destination "$Build\bin\x86\python\vcruntime140.dll" -Force
    }
    catch {
      Write-Host ("  ERROR: Failed to copy Visual C++ Runtime DLL." ) -ForegroundColor "Red"
    }

    # Q-Dir
    Write-Host "Extracting: Q-Dir"
    try {
      $ArgumentList = @(
        "x", "$Temp\qdir64.zip", "-o$Build\bin\amd64",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      Move-Item "$Build\bin\amd64\Q-Dir\Q-Dir_x64.exe" "$Build\bin\amd64\Q-Dir\Q-Dir.exe" -Force
      $ArgumentList = @(
        "x", "$Temp\qdir32.zip", "-o$Build\bin\x86",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # VirtIO Drivers
    Write-Host "Extracting: VirtIO Drivers"
    try {
      $ArgumentList = @(
        "e", "$Temp\virtio-win.iso", "-o$Build\Drivers\amd64\VirtIO",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "*\w10\amd64\*")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "e", "$Temp\virtio-win.iso", "-o$Build\Drivers\x86\VirtIO",
        "-aoa", "-bso0", "-bse0", "-bsp0",
        "*\w10\x86\*")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    # wimlib-imagex
    try {
      $ArgumentList = @(
        "x", "$Temp\wimlib64.zip", "-o$Build\bin\amd64\wimlib",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      $ArgumentList = @(
        "x", "$Temp\wimlib32.zip", "-o$Build\bin\x86\wimlib",
        "-aoa", "-bso0", "-bse0", "-bsp0")
      Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }

    ## Cleanup ##
    if (Ask-User "Delete temp files?") {
      Remove-Item "$Temp" -Recurse
    }
  }

  ## Build ##
  foreach ($Arch in @("amd64", "x86")) {
    $Drivers = "$Build\Drivers\$Arch"
    $Mount = "$Build\Mount"
    $PEFiles = "$Build\PEFiles\$Arch"

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
    Mount-WindowsImage -Path $Mount -ImagePath "$PEFiles\media\sources\boot.wim" -Index 1 -LogPath "$LogDir\DISM.log"

    # Add drivers
    Add-WindowsDriver -Path $Mount -Driver $Drivers -Recurse -LogPath "$LogDir\DISM.log"

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
      Add-WindowsPackage –PackagePath $PackagePath –Path $Mount -LogPath "$LogDir\DISM.log"
      $LangPackagePath = ("{0}\{1}\WinPE_OCs\en-us\{2}_en-us.cab" -f $Env:WinPERoot, $Arch, $Package)
      if (Test-Path $LangPackagePath) {
        Add-WindowsPackage –PackagePath $LangPackagePath –Path $Mount -LogPath "$LogDir\DISM.log"
      }
    }

    # Set RamDisk size
    $ArgumentList = @(
      ('/Image:"{0}"' -f $Mount),
      "/Set-ScratchSpace:512",
      ('/LogPath:"{0}\DISM.log"' -f $LogDir)
    )
    Start-Process -FilePath $DISM -ArgumentList $ArgumentList -NoNewWindow -Wait

    # Add tools
    Write-Host "Copying tools..."
    Copy-Item -Path "$Build\bin\$Arch" -Destination "$Mount\.bin" -Recurse -Force
    Copy-Item -Path "$Root\.pe_items\_include\*" -Destination "$Mount\.bin" -Recurse -Force
    if ($Arch -eq "amd64") {
      $DestIni = "$Mount\.bin\HWiNFO\HWiNFO64.INI"
    } else {
      $DestIni = "$Mount\.bin\HWiNFO\HWiNFO32.INI"
    }
    Move-Item -Path "$Mount\.bin\HWiNFO\HWiNFO.INI" -Destination $DestIni -Force
    Copy-Item -Path "$Root\Images\WinPE.jpg" -Destination "$Mount\.bin\ConEmu\ConEmu.jpg" -Recurse -Force
    Copy-Item -Path "$Bin\Scripts" -Destination "$Mount\.bin\Scripts" -Recurse -Force
    Copy-Item -Path "$Build\main.py" -Destination "$Mount\.bin\Scripts\settings\main.py" -Force

    # Add System32 items
    $HostSystem32 = "{0}\System32" -f $Env:SystemRoot
    Copy-Item -Path "$Root\.pe_items\System32\*" -Destination "$Mount\Windows\System32" -Recurse -Force
    $ArgumentList = @("/f", "$Mount\Windows\System32\winpe.jpg", "/a")
    Start-Process -FilePath "$HostSystem32\takeown.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
    $ArgumentList = @("$Mount\Windows\System32\winpe.jpg", "/grant", "Administrators:F")
    Start-Process -FilePath "$HostSystem32\icacls.exe" -ArgumentList $ArgumentList -NoNewWindow -Wait
    Copy-Item -Path "$Root\Images\WinPE.jpg" -Destination "$Mount\Windows\System32\winpe.jpg" -Recurse -Force

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
    Dismount-WindowsImage -Path $Mount -Save -LogPath "$LogDir\DISM.log"

    # Create ISO
    New-Item -Type Directory "$Root\OUT_PE" 2>&1 | Out-Null
    $ArgumentList = @("/iso", $PEFiles, "$Root\OUT_PE\$KitNameShort-WinPE-$Date-$Arch.iso")
    $Cmd = "{0}\MakeWinPEMedia.cmd" -f $Env:WinPERoot
    Start-Process -FilePath $Cmd -ArgumentList $ArgumentList -NoNewWindow -Wait
  }

  ## Cleanup ##
  Remove-Item -Path "$Build\Mount" -Recurse -Force
  Remove-Item -Path "$Build\PEFiles" -Recurse -Force

  ## Done ##
  Pop-Location
  Write-Host "`nDone."
  WKPause "Press Enter to exit... "
}
