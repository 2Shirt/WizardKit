# Wizard Kit: Windows PE Build Tool

## Init ##
#Requires -Version 3.0
#Requires -RunAsAdministrator 
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Windows PE Build Tool"
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
$bin = (Get-Item $wd -Force).Parent.FullName
$root = (Get-Item $bin -Force).Parent.FullName
$tmp = "{0}\tmp" -f $bin
$errors = 0
pushd "$wd"
$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "white"
$progressPreference = 'silentlyContinue'
# clear
foreach ($v in @('SystemDrive', 'USERPROFILE', 'DISMRoot', 'BCDBootRoot', 'ImagingRoot', 'OSCDImgRoot', 'WdsmcastRoot')) {
    write-host ('{0}: {1}' -f $v, (gci env:$v).value)
}
write-host ""
write-host ("wd:   {0}" -f $wd)
write-host ("bin:  {0}" -f $bin)
write-host ("root: {0}" -f $root)
write-host ("tmp:  {0}" -f $tmp)
read-host "Bananas?"
exit

## Functions ##
function download-file {
    param ([String]$path, [String]$name, [String]$url)
    $outfile = "{0}\{1}" -f $path, $name

    Write-Host ("Downloading: {0}" -f $name)
    New-Item -Type Directory $path 2>&1 | Out-Null
    try {
        invoke-webrequest -uri $url -outfile $outfile
    }
    catch {
        Write-Host ("  ERROR: Failed to download file." ) -foregroundcolor "Red"
        $errors += 1
    }
}
function find-dynamic-url {
    param ([String]$source_page, [String]$regex)
    $d_url = ""

    # Get source page
    invoke-webrequest -uri $source_page -outfile "tmp_page"

    # Search for real url
    $d_url = Get-Content "tmp_page" | Where-Object {$_ -imatch $regex}
    $d_url = $d_url -ireplace '.*(a |)href="([^"]+)".*', '$2'
    $d_url = $d_url -ireplace ".*(a |)href='([^']+)'.*", '$2'

    # Remove tmp_page
    Remove-Item "tmp_page"

    return $d_url
}
function wk_pause {
    param([string]$message = "Press Enter to continue... ")
    Write-Host $message
    $x = read-host
}

## Build ##
# TODO #

## Done ##
popd
