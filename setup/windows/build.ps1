# Wizard Kit: Build base kit

## Init ##
#Requires -Version 3.0
[CmdletBinding()]
Param(
  [Parameter(Mandatory=$True)]
    [string]$KitPath
)
if (Test-Path Env:\DEBUG) {
  Set-PSDebug -Trace 1
}
$Host.UI.RawUI.WindowTitle = "Wizard Kit: Build Tool"
$WD = Split-Path $MyInvocation.MyCommand.Path | Get-Item
$Root = Get-Item "$KitPath"
$Bin = Get-Item "$($Root.FullName)\.bin" -Force
$Temp = "$Bin\tmp"
$System32 = "{0}\System32" -f $Env:SystemRoot
$SysWOW64 = "{0}\SysWOW64" -f $Env:SystemRoot
Push-Location "$WD"
$Host.UI.RawUI.BackgroundColor = "black"
$Host.UI.RawUI.ForegroundColor = "white"
#Enable TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12


## Functions ##
function Abort {
  Write-Host -ForegroundColor "Red" "`nAborted."
  WKPause "Press Enter to exit..."
  exit
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

## Safety Check ##
if ($PSVersionTable.PSVersion.Major -eq 6 -and $PSVersionTable.OS -imatch "Windows 6.1") {
  Write-Host "`nThis script doesn't support PowerShell 6.0 on Windows 7."
	Write-Host "Press Enter to exit... " -NoNewLine
  Abort
}

## PowerShell equivalent of Python's "if __name__ == '__main__'"
# Code based on StackOverflow comments
# Question:     https://stackoverflow.com/q/4693947
# Using answer: https://stackoverflow.com/a/5582692
# Asked by:     https://stackoverflow.com/users/65164/mark-mascolino
# Answer by:    https://stackoverflow.com/users/696808/bacon-bits
if ($MyInvocation.InvocationName -ne ".") {
  Clear-Host
  Write-Host "Wizard Kit: Build Tool`n`n`n`n`n"

  ## Sources ##
  $Sources = Get-Content -Path "$WD\sources.json" | ConvertFrom-JSON

  ## Download ##
  $DownloadErrors = 0

  # 7-Zip
  DownloadFile -Path $Temp -Name "7z-installer.msi" -Url $Sources.'7-Zip Installer'
  DownloadFile -Path $Temp -Name "7z-extra.7z" -Url $Sources.'7-Zip Extra'

  # ConEmu
  DownloadFile -Path $Temp -Name "ConEmuPack.7z" -Url $Sources.'ConEmu'

  # Python
  DownloadFile -Path $Temp -Name "python32.zip" -Url $Sources.'Python x32'
  DownloadFile -Path $Temp -Name "python64.zip" -Url $Sources.'Python x64'

  # Python: docopt
  Copy-Item -Path "$WD\docopt\docopt-0.6.2-py2.py3-none-any.whl" -Destination "$Temp\docopt.whl"

  # Python: psutil
  $DownloadPage = "https://pypi.org/project/psutil/"
  $RegEx = "href=.*-cp38-cp38-win32.whl"
  $Url = FindDynamicUrl $DownloadPage $RegEx
  DownloadFile -Path $Temp -Name "psutil32.whl" -Url $Url
  $RegEx = "href=.*-cp38-cp38-win_amd64.whl"
  $Url = FindDynamicUrl $DownloadPage $RegEx
  DownloadFile -Path $Temp -Name "psutil64.whl" -Url $Url

  # Python: pytz, requests, & dependancies
  $RegEx = "href=.*.py3-none-any.whl"
  foreach ($Module in @("chardet", "certifi", "idna", "pytz", "urllib3", "requests")) {
    $DownloadPage = "https://pypi.org/project/$Module/"
    $Name = "$Module.whl"
    $Url = FindDynamicUrl -SourcePage $DownloadPage -RegEx $RegEx
    DownloadFile -Path $Temp -Name $Name -Url $Url
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
    Start-Process -FilePath "$System32\msiexec.exe" -ArgumentList $ArgumentList -Wait
    $SevenZip = "$Temp\7zi\Files\7-Zip\7z.exe"
    $ArgumentList = @(
      "x", "$Temp\7z-extra.7z", "-o$Bin\7-Zip",
      "-aoa", "-bso0", "-bse0", "-bsp0",
      "-x!x64\*.dll", "-x!Far", "-x!*.dll")
    Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    Start-Sleep 1
    Move-Item "$Bin\7-Zip\x64\7za.exe" "$Bin\7-Zip\7za64.exe"
    Remove-Item "$Bin\7-Zip\x64" -Recurse
    Remove-Item "$Temp\7z*" -Recurse
    $SevenZip = "$Bin\7-Zip\7za.exe"
  }
  catch {
    Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
  }

  # ConEmu
  Write-Host "Extracting: ConEmu"
  try {
    $ArgumentList = @(
      "x", "$Temp\ConEmuPack.7z", "-o$Bin\ConEmu",
      "-aoa", "-bso0", "-bse0", "-bsp0")
    Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
    Remove-Item "$Temp\ConEmuPack.7z"
  }
  catch {
    Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
  }

  # Python
  foreach ($Arch in @("32", "64")) {
    Write-Host "Extracting: Python (x$Arch)"
    $Files = @(
      "python$Arch.zip",
      "certifi.whl",
      "chardet.whl",
      "docopt.whl",
      "idna.whl",
      "pytz.whl",
      "psutil$Arch.whl",
      "requests.whl",
      "urllib3.whl"
    )
    try {
      foreach ($File in $Files) {
        $ArgumentList = @(
          "x", "$Temp\$File", "-o$Bin\Python\x$Arch",
          "-aoa", "-bso0", "-bse0", "-bsp0")
        Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
      }
    }
    catch {
      Write-Host ("  ERROR: Failed to extract files." ) -ForegroundColor "Red"
    }
  }
  Remove-Item "$Temp\python*.zip"
  Remove-Item "$Temp\*.whl"

  ## Done ##
  Pop-Location
  $ArgumentList = @("-run", "$Bin\Python\x32\python.exe", "$Bin\Scripts\build_kit_windows.py", "-new_console:n")
  Start-Process -FilePath "$Bin\ConEmu\ConEmu.exe" -ArgumentList $ArgumentList -verb RunAs
}
