# Wizard Kit: Download the latest versions of the programs in the kit

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Kit Update Tool"
$bin = (Get-Item $wd).Parent.FullName
$curl = "$bin\curl\curl.exe"
$sz = "$bin\7-Zip\7za.exe"

# OS Check
. .\check_os.ps1
if ($arch -eq 64) {
    $sz = "$bin\7-Zip\7za64.exe"
}

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
start $sz -argumentlist @("e", "`"$bin\_Drivers\Samsung Magician.zip`"", "-aoa", "-bso0", "-bsp0", "-o$bin\_Drivers") -nonewwindow -wait
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

## Installers ##
$path = (Get-Item $wd).Parent.Parent.FullName
$path = "$path\Installers"

# Ninite - Main
download-file "$path" "MSE.exe" "https://ninite.com/essentials/ninite.exe"
download-file "$path" "Runtimes.exe" "https://ninite.com/.net4.6.2-air-java8-silverlight/ninite.exe"
download-file "$path" "Win7.exe" "https://ninite.com/.net4.6.2-7zip-air-chrome-firefox-java8-silverlight-vlc/ninite.exe"
download-file "$path" "Win8.exe" "https://ninite.com/.net4.6.2-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc/ninite.exe"
download-file "$path" "Win10.exe" "https://ninite.com/.net4.6.2-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc/ninite.exe"

# Ninite - Audio-Video
download-file "$path\Extras\Audio-Video" "AIMP.exe" "https://ninite.com/aimp/ninite.exe"
download-file "$path\Extras\Audio-Video" "Audacity.exe" "https://ninite.com/audacity/ninite.exe"
download-file "$path\Extras\Audio-Video" "CCCP.exe" "https://ninite.com/cccp/ninite.exe"
download-file "$path\Extras\Audio-Video" "Foobar2000.exe" "https://ninite.com/foobar/ninite.exe"
download-file "$path\Extras\Audio-Video" "GOM.exe" "https://ninite.com/gom/ninite.exe"
download-file "$path\Extras\Audio-Video" "iTunes.exe" "https://ninite.com/itunes/ninite.exe"
download-file "$path\Extras\Audio-Video" "K-Lite Codecs.exe" "https://ninite.com/klitecodecs/ninite.exe"
download-file "$path\Extras\Audio-Video" "KMPlayer.exe" "https://ninite.com/kmplayer/ninite.exe"
download-file "$path\Extras\Audio-Video" "MediaMonkey.exe" "https://ninite.com/mediamonkey/ninite.exe"
download-file "$path\Extras\Audio-Video" "MusicBee.exe" "https://ninite.com/musicbee/ninite.exe"
download-file "$path\Extras\Audio-Video" "Spotify.exe" "https://ninite.com/spotify/ninite.exe"
download-file "$path\Extras\Audio-Video" "VLC.exe" "https://ninite.com/vlc/ninite.exe"
download-file "$path\Extras\Audio-Video" "Winamp.exe" "https://ninite.com/winamp/ninite.exe"

# Ninite - Cloud Storage
download-file "$path\Extras\Cloud Storage" "BitTorrent Sync.exe" "https://ninite.com/bittorrentsync/ninite.exe"
download-file "$path\Extras\Cloud Storage" "Dropbox.exe" "https://ninite.com/dropbox/ninite.exe"
download-file "$path\Extras\Cloud Storage" "Google Drive.exe" "https://ninite.com/googledrive/ninite.exe"
download-file "$path\Extras\Cloud Storage" "Mozy.exe" "https://ninite.com/mozy/ninite.exe"
download-file "$path\Extras\Cloud Storage" "OneDrive.exe" "https://ninite.com/onedrive/ninite.exe"
download-file "$path\Extras\Cloud Storage" "SugarSync.exe" "https://ninite.com/sugarsync/ninite.exe"

# Ninite - Communication
download-file "$path\Extras\Communication" "AIM.exe" "https://ninite.com/aim/ninite.exe"
download-file "$path\Extras\Communication" "Pidgin.exe" "https://ninite.com/pidgin/ninite.exe"
download-file "$path\Extras\Communication" "Skype.exe" "https://ninite.com/skype/ninite.exe"
download-file "$path\Extras\Communication" "Trillian.exe" "https://ninite.com/trillian/ninite.exe"

# Ninite - Compression
download-file "$path\Extras\Compression" "7-Zip.exe" "https://ninite.com/7zip/ninite.exe"
download-file "$path\Extras\Compression" "PeaZip.exe" "https://ninite.com/peazip/ninite.exe"
download-file "$path\Extras\Compression" "WinRAR.exe" "https://ninite.com/winrar/ninite.exe"

# Ninite - Developer
download-file "$path\Extras\Developer" "Eclipse.exe" "https://ninite.com/eclipse/ninite.exe"
download-file "$path\Extras\Developer" "FileZilla.exe" "https://ninite.com/filezilla/ninite.exe"
download-file "$path\Extras\Developer" "JDK 8.exe" "https://ninite.com/jdk8/ninite.exe"
download-file "$path\Extras\Developer" "JDK 8 (x64).exe" "https://ninite.com/jdkx8/ninite.exe"
download-file "$path\Extras\Developer" "Notepad++.exe" "https://ninite.com/notepadplusplus/ninite.exe"
download-file "$path\Extras\Developer" "PuTTY.exe" "https://ninite.com/putty/ninite.exe"
download-file "$path\Extras\Developer" "Python 2.exe" "https://ninite.com/python/ninite.exe"
download-file "$path\Extras\Developer" "Visual Studio Code.exe" "https://ninite.com/vscode/ninite.exe"
download-file "$path\Extras\Developer" "WinMerge.exe" "https://ninite.com/winmerge/ninite.exe"
download-file "$path\Extras\Developer" "WinSCP.exe" "https://ninite.com/winscp/ninite.exe"

# Ninite - File Sharing
download-file "$path\Extras\File Sharing" "eMule.exe" "https://ninite.com/emule/ninite.exe"
download-file "$path\Extras\File Sharing" "qBittorrent.exe" "https://ninite.com/qbittorrent/ninite.exe"

# Ninite - Image-Photo
download-file "$path\Extras\Image-Photo" "FastStone.exe" "https://ninite.com/faststone/ninite.exe"
download-file "$path\Extras\Image-Photo" "GIMP.exe" "https://ninite.com/gimp/ninite.exe"
download-file "$path\Extras\Image-Photo" "Greenshot.exe" "https://ninite.com/greenshot/ninite.exe"
download-file "$path\Extras\Image-Photo" "Inkscape.exe" "https://ninite.com/inkscape/ninite.exe"
download-file "$path\Extras\Image-Photo" "IrfanView.exe" "https://ninite.com/irfanview/ninite.exe"
download-file "$path\Extras\Image-Photo" "Paint.NET.exe" "https://ninite.com/paint.net/ninite.exe"
download-file "$path\Extras\Image-Photo" "ShareX.exe" "https://ninite.com/sharex/ninite.exe"
download-file "$path\Extras\Image-Photo" "XnView.exe" "https://ninite.com/xnview/ninite.exe"

# Ninite - Misc
download-file "$path\Extras\Misc" "Classic Start.exe" "https://ninite.com/classicstart/ninite.exe"
download-file "$path\Extras\Misc" "Evernote.exe" "https://ninite.com/evernote/ninite.exe"
download-file "$path\Extras\Misc" "Everything.exe" "https://ninite.com/everything/ninite.exe"
download-file "$path\Extras\Misc" "Google Earth.exe" "https://ninite.com/googleearth/ninite.exe"
download-file "$path\Extras\Misc" "NV Access.exe" "https://ninite.com/nvda/ninite.exe"
download-file "$path\Extras\Misc" "Steam.exe" "https://ninite.com/steam/ninite.exe"

# Ninite - Office
download-file "$path\Extras\Office" "CutePDF.exe" "https://ninite.com/cutepdf/ninite.exe"
download-file "$path\Extras\Office" "Foxit Reader.exe" "https://ninite.com/foxit/ninite.exe"
download-file "$path\Extras\Office" "LibreOffice.exe" "https://ninite.com/libreoffice/ninite.exe"
download-file "$path\Extras\Office" "OpenOffice.exe" "https://ninite.com/openoffice/ninite.exe"
download-file "$path\Extras\Office" "PDFCreator.exe" "https://ninite.com/pdfcreator/ninite.exe"
download-file "$path\Extras\Office" "SumatraPDF.exe" "https://ninite.com/sumatrapdf/ninite.exe"
download-file "$path\Extras\Office" "Thunderbird.exe" "https://ninite.com/thunderbird/ninite.exe"

# Ninite - Runtimes
download-file "$path\Extras\Runtimes" "dotNET.exe" "https://ninite.com/.net4.6.2/ninite.exe"
download-file "$path\Extras\Runtimes" "Adobe Air.exe" "https://ninite.com/air/ninite.exe"
download-file "$path\Extras\Runtimes" "Java 8.exe" "https://ninite.com/java8/ninite.exe"
download-file "$path\Extras\Runtimes" "Shockwave.exe" "https://ninite.com/shockwave/ninite.exe"
download-file "$path\Extras\Runtimes" "Silverlight.exe" "https://ninite.com/silverlight/ninite.exe"

# Ninite - Security
download-file "$path\Extras\Security" "Ad-Aware.exe" "https://ninite.com/adaware/ninite.exe"
download-file "$path\Extras\Security" "Avast.exe" "https://ninite.com/avast/ninite.exe"
download-file "$path\Extras\Security" "AVG.exe" "https://ninite.com/avg/ninite.exe"
download-file "$path\Extras\Security" "Avira.exe" "https://ninite.com/avira/ninite.exe"
download-file "$path\Extras\Security" "Microsoft Security Essentials.exe" "https://ninite.com/essentials/ninite.exe"
download-file "$path\Extras\Security" "Malwarebytes Anti-Malware.exe" "https://ninite.com/malwarebytes/ninite.exe"
download-file "$path\Extras\Security" "Spybot 2.exe" "https://ninite.com/spybot2/ninite.exe"
download-file "$path\Extras\Security" "SUPERAntiSpyware.exe" "https://ninite.com/super/ninite.exe"

# Ninite - Utilities
download-file "$path\Extras\Utilities" "Auslogics DiskDefrag.exe" "https://ninite.com/auslogics/ninite.exe"
download-file "$path\Extras\Utilities" "CDBurnerXP.exe" "https://ninite.com/cdburnerxp/ninite.exe"
download-file "$path\Extras\Utilities" "Glary Utilities.exe" "https://ninite.com/glary/ninite.exe"
download-file "$path\Extras\Utilities" "ImgBurn.exe" "https://ninite.com/imgburn/ninite.exe"
download-file "$path\Extras\Utilities" "InfraRecorder.exe" "https://ninite.com/infrarecorder/ninite.exe"
download-file "$path\Extras\Utilities" "KeePass 2.exe" "https://ninite.com/keepass2/ninite.exe"
download-file "$path\Extras\Utilities" "Launchy.exe" "https://ninite.com/launchy/ninite.exe"
download-file "$path\Extras\Utilities" "RealVNC.exe" "https://ninite.com/realvnc/ninite.exe"
download-file "$path\Extras\Utilities" "Revo Uninstaller.exe" "https://ninite.com/revo/ninite.exe"
download-file "$path\Extras\Utilities" "TeamViewer 11.exe" "https://ninite.com/teamviewer11/ninite.exe"
download-file "$path\Extras\Utilities" "TeraCopy.exe" "https://ninite.com/teracopy/ninite.exe"
download-file "$path\Extras\Utilities" "WinDirStat.exe" "https://ninite.com/windirstat/ninite.exe"

# Ninite - Web Browsers
download-file "$path\Extras\Web Browsers" "Google Chrome.exe" "https://ninite.com/chrome/ninite.exe"
download-file "$path\Extras\Web Browsers" "Firefox.exe" "https://ninite.com/firefox/ninite.exe"
download-file "$path\Extras\Web Browsers" "Opera.exe" "https://ninite.com/operaChromium/ninite.exe"

## Done ##
popd
pause "Press Enter to exit..."
