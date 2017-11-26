# Wizard Kit: Windows PE Build Tool

## Init ##
#Requires -Version 3.0
#Requires -RunAsAdministrator 
Clear-Host
$Host.UI.RawUI.WindowTitle = "Wizard Kit: Windows PE Build Tool"
$WD = $(Split-Path $MyInvocation.MyCommand.Path)
$Bin = (Get-Item $WD -Force).Parent.FullName
$Root = (Get-Item $Bin -Force).Parent.FullName
$Temp = "{0}\tmp" -f $Bin
$Errors = 0
Push-Location "$WD"
$Host.UI.RawUI.BackgroundColor = "black"
$Host.UI.RawUI.ForegroundColor = "white"
$ProgressPreference = 'silentlyContinue'
# Clear-Host
foreach ($Var in @('SystemDrive', 'USERPROFILE', 'DISMRoot', 'BCDBootRoot', 'ImagingRoot', 'OSCDImgRoot', 'WdsmcastRoot')) {
    Write-Host ('{0}: {1}' -f $Var, (Get-ChildItem Env:$Var).Value)
}
Write-Host ""
Write-Host ("wd:   {0}" -f $WD)
Write-Host ("bin:  {0}" -f $Bin)
Write-Host ("root: {0}" -f $Root)
Write-Host ("tmp:  {0}" -f $Temp)
Read-Host "Bananas?"
exit

## Functions ##
function Download-File {
    param ([String]$Path, [String]$Name, [String]$Url)
    $OutFile = "{0}\{1}" -f $Path, $Name

    Write-Host ("Downloading: {0}" -f $Name)
    New-Item -Type Directory $Path 2>&1 | Out-Null
    try {
        Invoke-Webrequest -Uri $Url -OutFile $OutFile
    }
    catch {
        Write-Host ("  ERROR: Failed to download file." ) -ForegroundColor "Red"
        $Errors += 1
    }
}
function Find-DynamicUrl {
    param ([String]$SourcePage, [String]$RegEx)
    $Url = ""

    # Get source page
    Invoke-Webrequest -Uri $SourcePage -OutFile "tmp_page"

    # Search for real url
    $Url = Get-Content "tmp_page" | Where-Object {$_ -imatch $RegEx}
    $Url = $Url -ireplace '.*(a |)href="([^"]+)".*', '$2'
    $Url = $Url -ireplace ".*(a |)href='([^']+)'.*", '$2'

    # Remove tmp_page
    Remove-Item "tmp_page"

    return $Url
}
function WK-Pause {
    param([string]$Message = "Press Enter to continue... ")
    Write-Host $Message
    Read-Host
}

## Build ##
# TODO #

## Done ##
Pop-Location
