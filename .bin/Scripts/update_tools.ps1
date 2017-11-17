# Wizard-Kit-Updater

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit Update Tool"
$bin = (Get-Item $wd).Parent.FullName
$curl = "$bin\curl\curl.exe"

## Functions ##
function download-file {
    param ([String]$path, [String]$name, [String]$url)
	$output = "{0}\{1}" -f $path, $name
    
    write-host ("Downloading {0}" -f $name)
    New-Item -Type Directory $path 2>&1 | Out-Null
    start "$curl" -argumentlist @("-#LSfo", "`"$output`"", "`"$url`"") -nonewwindow -wait
}
function find-dynamic-url {
    param ([String]$source_page, [String]$regex)
    $d_url = ""
    
    # Get source page
    start "$curl" -argumentlist @("-Lfso", "tmp_page", "`"$source_page`"") -nonewwindow -wait
    
    # Search for real url
    $d_url = Get-Content "tmp_page" | Where-Object {$_ -imatch $regex}
    $d_url = $d_url -ireplace '.*(a |)href="([^"]+)".*', '$2'
    $d_url = $d_url -ireplace ".*(a |)href='([^']+)'.*", '$2'
	
	# Remove tmp_page
	Remove-Item "tmp_page"
    
    return $d_url
}

## Diagnostics ##
# HitmanPro
$path = "$bin\HitmanPro"
$name = "HitmanPro.exe"
$url = "http://dl.surfright.nl/HitmanPro.exe"
download-file $path $name $url
$name = "HitmanPro64.exe"
$url = "http://dl.surfright.nl/HitmanPro_x64.exe"
download-file $path $name $url

## VR-OSR ##
# AdwCleaner
$path = "$bin"
$name = "AdwCleaner.exe"
$dl_page = "http://www.bleepingcomputer.com/download/adwcleaner/dl/125/"
$regex = "href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/a/adwcleaner/AdwCleaner\.exe"
$url = find-dynamic-url $dl_page $regex
download-file $path $name $url

# ESET Online Scanner
$path = "$bin"
$name = "ESET.exe"
$url = "http://download.eset.com/special/eos/esetsmartinstaller_enu.exe"
download-file $path $name $url

# Junkware Removal Tool
$path = "$bin"
$name = "JRT.exe"
$url = "http://downloads.malwarebytes.org/file/jrt"
download-file $path $name $url

# Kaspersky Virus Removal Tool
$path = "$bin"
$name = "KVRT.exe"
$url = "http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe"
download-file $path $name $url

# RKill
$path = "$bin\RKill"
$name = "RKill.exe"
$dl_page = "http://www.bleepingcomputer.com/download/rkill/dl/10/"
$regex = "href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/r/rkill/rkill\.exe"
$url = find-dynamic-url $dl_page $regex
download-file $path $name $url

# TDSSKiller
$path = "$bin"
$name = "TDSSKiller.exe"
$url = "http://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe"
download-file $path $name $url

## Driver Tools ##
# Acer Serial Number Detect Tool
$path = "$bin\_Drivers"
$name = "Acer Serial Number Detect Tool.exe"
$url = "http://global-download.acer.com/SupportFiles/Files/SNID/APP/SerialNumberDetectionTool.exe"
download-file $path $name $url

# AMD Autodetect
$path = "$bin\_Drivers"
$name = "AMD Autodetect.exe"
$url = "http://www2.ati.com/drivers/auto/autodetectutility.exe"
download-file $path $name $url

# AMD Gaming Evolved
$path = "$bin\_Drivers"
$name = "AMD Gaming Evolved.exe"
$url = "http://clientupdater.raptr.com/client/pc/amd/raptr_installer.exe"
download-file $path $name $url

# Dell System Detect
$path = "$bin\_Drivers"
$name = "Dell System Detect.exe"
$url = "https://downloads.dell.com/tools/dellsystemdetect/dellsystemdetectlauncher.exe"
download-file $path $name $url

# GeForce Experience
$path = "$bin\_Drivers"
$name = "GeForce Experience.exe"
$dl_page = "http://www.geforce.com/geforce-experience/download"
$regex = "href=.*http(s|)://us\.download\.nvidia\.com/GFE/GFEClient/[0-9\.]+/GeForce_Experience_v[0-9\.]+\.exe"
$url = find-dynamic-url $dl_page $regex
download-file $path $name $url

# HP Support Solutions Framework
$path = "$bin\_Drivers"
$name = "HP Support Solutions Framework.exe"
$url = "http://h20614.www2.hp.com/ediags/filehosting/api/installer"
download-file $path $name $url

# Intel Driver Update Utility
$path = "$bin\_Drivers"
$name = "Intel Driver Update Utility.exe"
$dl_page = "http://www.intel.com/content/www/us/en/support/detect.html"
$regex = "a href.*http(s|)://downloadmirror\.intel\.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+/Intel%20Driver%20Update%20Utility%20Installer.exe"
$url = find-dynamic-url $dl_page $regex
$url = find-dynamic-url $dl_page $regex
download-file $path $name $url

# Intel SSD Toolbox
$path = "$bin\_Drivers"
$name = "Intel SSD Toolbox.exe"
$dl_page = "https://downloadcenter.intel.com/download/26085/Intel-Solid-State-Drive-Toolbox"
$regex = "href=./downloads/eula/[0-9]+/Intel-Solid-State-Drive-Toolbox.httpDown=https\%3A\%2F\%2Fdownloadmirror\.intel\.com\%2F[0-9]+\%2Feng\%2FIntel\%20SSD\%20Toolbox\%20-\%20v[0-9\.]+.exe"
$url = find-dynamic-url $dl_page $regex
$url = $url -ireplace '.*httpDown=(.*)', '$1'
$url = $url -ireplace '%3A', ':'
$url = $url -ireplace '%2F', '/'
download-file $path $name $url

# Lenovo Service Bridge
$path = "$bin\_Drivers"
$name = "Lenovo Service Bridge.exe"
$url = "https://download.lenovo.com/lsb/LSBsetup.exe"
download-file $path $name $url

# Samsung Magician
$path = "$bin\_Drivers"
$name = "Samsung Magician.zip"
$dl_page = "http://www.samsung.com/semiconductor/minisite/ssd/download/tools.html"
$regex = "href=./semiconductor/minisite/ssd/downloads/software/Samsung_Magician_Setup_v[0-9]+.zip"
$url = "http://www.samsung.com{0}" -f (find-dynamic-url $dl_page $regex)
download-file $path $name $url
start "$bin\7-Zip\7z.exe" -argumentlist @("e", "`"$bin\_Drivers\Samsung Magician.zip`"", "-aoa", "-bso0", "-bsp0", "-o$bin\_Drivers") -nonewwindow -wait
Remove-Item "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null
Remove-Item "$bin\_Drivers\Samsung Magician.zip" $path 2>&1 | Out-Null
Move-Item "$bin\_Drivers\Samsung*exe" "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null

# SanDisk Express Cache
$path = "$bin\_Drivers"
$name = "SanDisk Express Cache.exe"
$url = "http://mp3support.sandisk.com/ReadyCache/ExpressCacheSetup.exe"
download-file $path $name $url

# Toshiba System Detect
$path = "$bin\_Drivers"
$name = "Toshiba System Detect.exe"
$url = "http://cdgenp01.csd.toshiba.com/content/support/downloads/GetProductInfo.exe"
download-file $path $name $url

## Done ##
popd
pause "Press Enter to exit..."
