# Wizard Kit: Download kit components

## Init ##
#Requires -Version 3.0
if (Test-Path Env:\DEBUG) {
    Set-PSDebug -Trace 1
}
$Host.UI.RawUI.WindowTitle = "Wizard Kit: Build Tool"
$WD = $(Split-Path $MyInvocation.MyCommand.Path)
$Bin = (Get-Item $WD).Parent.FullName
$Root = (Get-Item $Bin -Force).Parent.FullName
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
    
    ## Download ##
    $DownloadErrors = 0
    $Path = $Temp

    # 7-Zip
    DownloadFile -Path $Path -Name "7z-installer.msi" -Url "https://www.7-zip.org/a/7z1805.msi"
    DownloadFile -Path $Path -Name "7z-extra.7z" -Url "https://www.7-zip.org/a/7z1805-extra.7z"

    # ConEmu
    $Url = "https://github.com/Maximus5/ConEmu/releases/download/v18.06.26/ConEmuPack.180626.7z"
    DownloadFile -Path $Path -Name "ConEmuPack.7z" -Url $Url

    # Notepad++
    $Url = "https://notepad-plus-plus.org/repository/7.x/7.5.8/npp.7.5.8.bin.minimalist.7z"
    DownloadFile -Path $Path -Name "npp.7z" -Url $Url

    # Python
    $Url = "https://www.python.org/ftp/python/3.7.0/python-3.7.0-embed-win32.zip"
    DownloadFile -Path $Path -Name "python32.zip" -Url $Url
    $Url = "https://www.python.org/ftp/python/3.7.0/python-3.7.0-embed-amd64.zip"
    DownloadFile -Path $Path -Name "python64.zip" -Url $Url

    # Python: psutil
    $DownloadPage = "https://pypi.org/project/psutil/"
    $RegEx = "href=.*-cp37-cp37m-win32.whl"
    $Url = FindDynamicUrl $DownloadPage $RegEx
    DownloadFile -Path $Path -Name "psutil32.whl" -Url $Url
    $RegEx = "href=.*-cp37-cp37m-win_amd64.whl"
    $Url = FindDynamicUrl $DownloadPage $RegEx
    DownloadFile -Path $Path -Name "psutil64.whl" -Url $Url

    # Python: requests & dependancies
    $RegEx = "href=.*.py3-none-any.whl"
    foreach ($Module in @("chardet", "certifi", "idna", "urllib3", "requests")) {
        $DownloadPage = "https://pypi.org/project/$Module/"
        $Name = "$Module.whl"
        $Url = FindDynamicUrl -SourcePage $DownloadPage -RegEx $RegEx
        DownloadFile -Path $Path -Name $Name -Url $Url
    }

    # Visual C++ Runtimes
    $Url = "https://aka.ms/vs/15/release/vc_redist.x86.exe"
    DownloadFile -Path $Path -Name "vcredist_x86.exe" -Url $Url
    $Url = "https://aka.ms/vs/15/release/vc_redist.x64.exe"
    DownloadFile -Path $Path -Name "vcredist_x64.exe" -Url $Url
    
    ## Bail ##
    # If errors were encountered during downloads
    if ($DownloadErrors -gt 0) {
        Abort
    }

    ## Install ##
    # Visual C++ Runtimes
    $ArgumentList = @("/install", "/passive", "/norestart")
    Start-Process -FilePath "$Temp\vcredist_x86.exe" -ArgumentList $ArgumentList -Wait
    Start-Process -FilePath "$Temp\vcredist_x64.exe" -ArgumentList $ArgumentList -Wait
    Remove-Item "$Temp\vcredist*.exe"
    
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

    # Notepad++
    Write-Host "Extracting: Notepad++"
    try {
        $ArgumentList = @(
            "x", "$Temp\npp.7z", "-o$Bin\NotepadPlusPlus",
            "-aoa", "-bso0", "-bse0", "-bsp0")
        Start-Process -FilePath $SevenZip -ArgumentList $ArgumentList -NoNewWindow -Wait
        Remove-Item "$Temp\npp.7z"
        Move-Item "$Bin\NotepadPlusPlus\notepad++.exe" "$Bin\NotepadPlusPlus\notepadplusplus.exe"
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
            "idna.whl",
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
    try {
        Copy-Item -Path "$System32\vcruntime140.dll" -Destination "$Bin\Python\x64\vcruntime140.dll" -Force
        Copy-Item -Path "$SysWOW64\vcruntime140.dll" -Destination "$Bin\Python\x32\vcruntime140.dll" -Force
    }
    catch {
        Write-Host ("  ERROR: Failed to copy Visual C++ Runtime DLLs." ) -ForegroundColor "Red"
    }
    Remove-Item "$Temp\python*.zip"
    Remove-Item "$Temp\*.whl"

    ## Configure ##
    Write-Host "Configuring kit"
    WKPause "Press Enter to open settings..."
    $Cmd = "$Bin\NotepadPlusPlus\notepadplusplus.exe"
    Start-Process -FilePath $Cmd -ArgumentList @("$Bin\Scripts\settings\main.py") -Wait
    Start-Sleep 1

    ## Done ##
    Pop-Location
    $ArgumentList = @("-run", "$Bin\Python\x32\python.exe", "$Bin\Scripts\update_kit.py", "-new_console:n")
    Start-Process -FilePath "$Bin\ConEmu\ConEmu.exe" -ArgumentList $ArgumentList -verb RunAs
}
