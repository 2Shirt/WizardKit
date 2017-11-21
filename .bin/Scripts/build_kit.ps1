# Wizard Kit: Download kit components

## Init ##
clear
$host.UI.RawUI.WindowTitle = "Wizard Kit: Build Tool"
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
$bin = (Get-Item $wd).Parent.FullName
$root = (Get-Item "$bin\..").FullName # Get-Item $bin fails
    # (I'm assuming that starting with a '.' is the issue)
$tmp = "{0}\tmp" -f $bin
$errors = 0
pushd "$wd"
$host.UI.RawUI.BackgroundColor = "black"
$host.UI.RawUI.ForegroundColor = "white"
$progressPreference = 'silentlyContinue'

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

## Download ##
$path = $tmp

# 7-Zip
$url = "http://www.7-zip.org/a/7z1701.msi"
download-file $path "7z-installer.msi" $url
$url = "http://www.7-zip.org/a/7z1701-extra.7z"
download-file $path "7z-extra.7z" $url

# ConEmu
$url = "https://github.com/Maximus5/ConEmu/releases/download/v17.11.09/ConEmuPack.171109.7z"
download-file $path "ConEmuPack.7z" $url

# Notepad++
$url = "https://notepad-plus-plus.org/repository/7.x/7.5.1/npp.7.5.1.bin.minimalist.7z"
download-file $path "npp.7z" $url

# Python
$url = "https://www.python.org/ftp/python/3.6.3/python-3.6.3-embed-win32.zip"
download-file $path "python32.zip" $url
$url = "https://www.python.org/ftp/python/3.6.3/python-3.6.3-embed-amd64.zip"
download-file $path "python64.zip" $url

# Python: psutil
$dl_page = "https://pypi.python.org/pypi/psutil"
$regex = "href=.*-cp36-cp36m-win32.whl"
$url = find-dynamic-url $dl_page $regex
download-file $path "psutil32.whl" $url
$regex = "href=.*-cp36-cp36m-win_amd64.whl"
$url = find-dynamic-url $dl_page $regex
download-file $path "psutil64.whl" $url

# Python: requests & dependancies
$regex = "href=.*.py3-none-any.whl"
foreach ($mod in @("chardet", "certifi", "idna", "urllib3", "requests")) {
    $dl_page = "https://pypi.python.org/pypi/{0}" -f $mod
    $name = "{0}.whl" -f $mod
    $url = find-dynamic-url $dl_page $regex
    download-file $path $name $url
}

## Extract ##
# 7-Zip
Write-Host "Extracting: 7-Zip"
try {
    start "msiexec" -argumentlist @("/a", "$tmp\7z-installer.msi", "TARGETDIR=$tmp\7zi", "/qn") -wait
    $sz = "$tmp\7zi\Files\7-Zip\7z.exe"
    start $sz -argumentlist @("x", "$tmp\7z-extra.7z", "-o$bin\7-Zip", "-aoa", "-bso0", "-bse0", "-bsp0", "-x!x64\*.dll", "-x!Far", "-x!*.dll") -nonewwindow -wait
    Start-Sleep 1
    Move-Item "$bin\7-Zip\x64\7za.exe" "$bin\7-Zip\7za64.exe"
    Remove-Item "$bin\7-Zip\x64" -Recurse
    Remove-Item "$tmp\7z*" -Recurse
    $sz = "$bin\7-Zip\7za.exe"
}
catch {
    Write-Host ("  ERROR: Failed to extract files." ) -foregroundcolor "Red"
}

# Notepad++
Write-Host "Extracting: Notepad++"
try {
    start $sz -argumentlist @("x", "$tmp\npp.7z", "-o$bin\NotepadPlusPlus", "-aoa", "-bso0", "-bse0", "-bsp0") -nonewwindow -wait
    Remove-Item "$tmp\npp.7z"
    Move-Item "$bin\NotepadPlusPlus\notepad++.exe" "$bin\NotepadPlusPlus\notepadplusplus.exe"
}
catch {
    Write-Host ("  ERROR: Failed to extract files." ) -foregroundcolor "Red"
}

# ConEmu
Write-Host "Extracting: ConEmu"
try {
    start $sz -argumentlist @("x", "$tmp\ConEmuPack.7z", "-o$bin\ConEmu", "-aoa", "-bso0", "-bse0", "-bsp0") -nonewwindow -wait
    Remove-Item "$tmp\ConEmuPack.7z"
}
catch {
    Write-Host ("  ERROR: Failed to extract files." ) -foregroundcolor "Red"
}

# Python x32
Write-Host "Extracting: Python (x32)"
try {
    foreach ($file in @("python32.zip", "certifi.whl", "chardet.whl", "idna.whl", "psutil32.whl", "requests.whl", "urllib3.whl")) {
        start $sz -argumentlist @("x", "$tmp\$file", "-o$bin\Python\x32", "-aoa", "-bso0", "-bse0", "-bsp0") -nonewwindow -wait
    }
}
catch {
    Write-Host ("  ERROR: Failed to extract files." ) -foregroundcolor "Red"
}

# Python x64
Write-Host "Extracting: Python (x64)"
try {
    foreach ($file in @("python64.zip", "certifi.whl", "chardet.whl", "idna.whl", "psutil64.whl", "requests.whl", "urllib3.whl")) {
         start $sz -argumentlist @("x", "$tmp\$file", "-o$bin\Python\x64", "-aoa", "-bso0", "-bse0", "-bsp0") -nonewwindow -wait
         }
    Remove-Item "$tmp\python*.zip"
    Remove-Item "$tmp\*.whl"
}
catch {
    Write-Host ("  ERROR: Failed to extract files." ) -foregroundcolor "Red"
}

## Configure ##
Write-Host "Configuring kit"
wk_pause "Press Enter to open settings..."
start "$bin\NotepadPlusPlus\notepadplusplus.exe" -argumentlist @("$bin\Scripts\settings\main.py") -wait
Start-Sleep 1

## Done ##
popd
if ($errors -gt 0) {
    wk_pause "Press Enter to exit..."
} else {
    start "$bin\ConEmu\ConEmu.exe" -argumentlist @("-run", "$bin\Python\x32\python.exe", "$bin\Scripts\update_kit.py", "-new_console:c") -verb Runas
}
