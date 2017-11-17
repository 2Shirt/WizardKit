# WK-Check Disk

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK / Chocolatey Installer"
$logpath = "$WKPath\Info\$date"
md "$logpath" 2>&1 | out-null
$log = "$logpath\Chocolatey.log"

# OS Check
. .\os_check.ps1

## Install/Upgrade Chocolatey ##
$choco = "$programdata\chocolatey\choco.exe"
if (test-path "$choco") {
    start "choco" -argumentlist @("upgrade", "chocolatey", "-y") -nonewwindow -wait
} else {
    .\install_chocolatey.ps1
}

## Sets ##
$sets = @(
        @("browsers", "Browsers"),
        @("compression", "Compression"),
        @("cloud", "Cloud"),
        @("office", "Office"),
        
        @("audio_video", "Audio / Video"),
        @("imaging", "Imaging / Photography"),
        @("gaming", "Gaming"),
        
        @("runtime", "Runtimes"),
        @("security", "Security"),
        
        @("misc", "Misc")
    )
$set_audio_video = @(
    @{ChocoName="itunes";                       ChocoArgs=""; Default=$false; DisplayName="iTunes"}
    @{ChocoName="mpv.install";                  ChocoArgs="youtube-dl";
                                                              Default=$true;  DisplayName="mpv"}
    @{ChocoName="spotify";                      ChocoArgs=""; Default=$false; DisplayName="Spotify"}
    @{ChocoName="vlc";                          ChocoArgs=""; Default=$true;  DisplayName="VLC"}
)
$set_browsers = @(
    @{ChocoName="googlechrome";                 ChocoArgs=""; Default=$true;  DisplayName="Google Chrome"}
    @{ChocoName="firefox";                      ChocoArgs=""; Default=$true;  DisplayName="Mozilla Firefox"}
    @{ChocoName="opera";                        ChocoArgs=""; Default=$false; DisplayName="Opera"}
)
$set_cloud = @(
    @{ChocoName="dropbox";                      ChocoArgs=""; Default=$false; DisplayName="Dropbox"}
    @{ChocoName="evernote";                     ChocoArgs=""; Default=$false; DisplayName="Evernote"}
    @{ChocoName="googledrive";                  ChocoArgs=""; Default=$false; DisplayName="Google Drive"}
)
$set_compression = @(
    @{ChocoName="7zip.install";                 ChocoArgs=""; Default=$true;  DisplayName="7-Zip"}
    @{ChocoName="peazip.install";               ChocoArgs=""; Default=$false; DisplayName="PeaZip"}
    @{ChocoName="winrar";                       ChocoArgs=""; Default=$false; DisplayName="WinRAR"}
)
$set_gaming = @(
    @{ChocoName="battle.net";                   ChocoArgs=""; Default=$false; DisplayName="Battle.net"}
    @{ChocoName="minecraft";                    ChocoArgs=""; Default=$false; DisplayName="Minecraft"}
    @{ChocoName="origin";                       ChocoArgs=""; Default=$false; DisplayName="Origin"}
    @{ChocoName="steam";                        ChocoArgs=""; Default=$false; DisplayName="Steam"}
)
$set_imaging = @(
    @{ChocoName="gimp";                         ChocoArgs=""; Default=$false; DisplayName="GIMP"}
    @{ChocoName="greenshot";                    ChocoArgs=""; Default=$false; DisplayName="Greenshot"}
    @{ChocoName="inkscape";                     ChocoArgs=""; Default=$false; DisplayName="Inkscape"}
    @{ChocoName="picasa";                       ChocoArgs=""; Default=$false; DisplayName="Picasa"}
    @{ChocoName="xnview";                       ChocoArgs=""; Default=$false; DisplayName="XnView"}
    @{ChocoName="xnviewmp.install";             ChocoArgs=""; Default=$false; DisplayName="XnViewMP"}
)
$set_misc = @(
    @{ChocoName="classic-shell";                ChocoArgs=@("-installArgs", "ADDLOCAL=ClassicStartMenu");
                                                              Default=$true;  DisplayName="Classic Start"}
    @{CRLF=$true; ChocoName="googleearth";      ChocoArgs=""; Default=$false; DisplayName="Google Earth"}
    @{CRLF=$true; ChocoName="keepass.install";  ChocoArgs=""; Default=$false; DisplayName="KeePass 2"}
    @{ChocoName="lastpass";                     ChocoArgs=""; Default=$false; DisplayName="LastPass"}
    @{CRLF=$true; ChocoName="skype";            ChocoArgs=""; Default=$false; DisplayName="Skype"}
)
$set_office = @(
    @{ChocoName="adobereader";                  ChocoArgs="adobereader-update";
                                                              Default=$true;  DisplayName="Adobe Reader DC"}
    @{CRLF=$true; ChocoName="libreoffice";      ChocoArgs="libreoffice-help";
                                                              Default=$false; DisplayName="LibreOffice"}
    @{ChocoName="openoffice";                   ChocoArgs=""; Default=$false; DisplayName="OpenOffice"}
    @{ChocoName="windowsessentials";            ChocoArgs=""; Default=$false; DisplayName="Windows Essentials 2012"}
    @{CRLF=$true; ChocoName="thunderbird";      ChocoArgs=""; Default=$false; DisplayName="Thunderbird"}
)
$set_runtime = @(
    @{ChocoName="adobeair";                     ChocoArgs=""; Default=$true;  DisplayName="Adobe Air"}
    @{ChocoName="jre8";                         ChocoArgs=""; Default=$true;  DisplayName="Java Runtime Environment"}
    @{ChocoName="silverlight";                  ChocoArgs=""; Default=$true;  DisplayName="Silverlight"}
    @{ChocoName="dotnet3.5";                    ChocoArgs=""; Default=$true;  DisplayName=".NET 3.5"}
    @{ChocoName="dotnet4.5.1";                  ChocoArgs=""; Default=$true;  DisplayName=".NET 4.5.1"}
)
$set_security = @(
    @{ChocoName="avastfreeantivirus";           ChocoArgs=""; Default=$false; DisplayName="Avast! Anti-Virus (Free)"}
    @{ChocoName="avgantivirusfree";             ChocoArgs=""; Default=$false; DisplayName="AVG Anti-Virus (Free)"}
    @{ChocoName="avirafreeantivirus";           ChocoArgs=""; Default=$false; DisplayName="Avira Anti-Virus (Free)"}
    @{ChocoName="kav";                          ChocoArgs=""; Default=$false; DisplayName="Kaspersky Anti-Virus"}
    @{ChocoName="malwarebytes";                 ChocoArgs=""; Default=$false; DisplayName="Malwarebytes Anti-Malware"}
    @{ChocoName="microsoftsecurityessentials";  ChocoArgs=""; Default=$true;  DisplayName="Microsoft Security Essentials"}
)

# Disable entries
if ($win_version -imatch '^(Vista|7)$') {
    $set_misc = $set_misc           | where {$_.DisplayName -inotmatch '(Classic Start)'}
}
if ($win_version -imatch '^(8|10)$') {
    $set_imaging = $set_imaging     | where {$_.DisplayName -inotmatch '(XnView)'}
    $set_security = $set_security   | where {$_.DisplayName -inotmatch '(Microsoft Security Essentials)'}
}

## Actions ##
$actions = @(
    @{Name="Select All"; Letter="A"}
    @{Name="Select Defaults"; Letter="D"}
    @{Name="Select None"; Letter="N"}
    @{Name="Accept Selection & Proceed"; Letter="P"; CRLF=$true}
    @{Name="Quit"; Letter="Q"}
)

function selection-loop {
    param([string]$name, $set)
    
    $selection = $null
    $proceed = $true
    do {
        # Update set
        foreach ($item in $set) {
            # Set default selection
            if (! $item.ContainsKey('Selected')) {
                $item.Selected = $item.Default
            }
            
            # Update name with selection indicator
            if ($item.Selected) {
                $item.Name = "* {0}" -f $item.DisplayName
            } else {
                $item.Name = "  {0}" -f $item.DisplayName
            }
        }
        
        # Get user input
        $selection = (menu-select $name "Please select which programs to install" $set $actions)
        
        # Perform action
        if ($selection -imatch '^[A]$') {
            # Select all
            foreach ($item in $set) {
                $item.Selected = $true
            }
        } elseif ($selection -imatch '^[D]$') {
            # Select defaults
            foreach ($item in $set) {
                $item.Selected = $item.Default
            }
        } elseif ($selection -imatch '^[N]$') {
            # Select none
            foreach ($item in $set) {
                $item.Selected = $false
            }
        } elseif ($selection -imatch '^[Q]$') {
            $proceed = $false
        } elseif ($selection -imatch '^\d+$') {
            # Toggle selection
            $selection -= 1
            $set[$selection].Selected = !($set[$selection].Selected)
        }
    } until ($selection -imatch '^[PQ]$')
    
    # Done
    if ($proceed) {
        return $set
    } else {
        throw
    }
}

## Network Check ##
wk-write "* Testing Internet Connection" "$log"
if (!(test-connection "google.com" -count 2 -quiet)) {
    wk-warn "System appears offline. Please connect to the internet." "$log"
    pause
    if (!(test-connection "google.com" -count 2 -quiet)) {
        wk-error "System still appears offline; aborting script." "$log"
        exit 1
    }
}

## Get selections ##
clear
if (ask ("Install default selections for Windows {0}?" -f $win_version)) {
    wk-write "Default Install" "$log"
    wk-write "" "$log"
    # Select defaults
    foreach ($s in $sets) {
        $set = get-variable -name ("set_{0}" -f $s[0]) -valueonly
    
        foreach ($prog in $set) {
            $prog.Selected = $prog.Default
        }
    }

} else {
    clear
    wk-write "Prepping Custom Install..." "$log"
    sleep -s 2
    
    try {
        foreach ($s in $sets) {
            $set = get-variable -name ("set_{0}" -f $s[0]) -valueonly
            $set = (selection-loop $s[1] $set.Clone())
        }
    } catch {
        wk-error "Installation Aborted" "$log"
        popd
        pause "Press Enter to exit..."
        exit
    }
}

## Install ##
foreach ($s in $sets | sort) {
    # wk-write ("Set: {0}" -f $s) "$log"
    $set = get-variable -name ("set_{0}" -f $s[0]) -valueonly
    
    foreach ($prog in $set | where {$_.Selected}) {
        wk-write ("Installing: {0}" -f $prog.DisplayName) "$log"
        if ($prog.ChocoArgs) {
            $prog.ChocoArgs = @("upgrade", "-y", $prog.ChocoName) + $prog.ChocoArgs
            start -wait "$programdata\chocolatey\choco.exe" -argumentlist $prog.ChocoArgs -nonewwindow
        } else {
            start -wait "$programdata\chocolatey\choco.exe" -argumentlist @("upgrade", "-y", $prog.ChocoName) -nonewwindow
        }
    }
}

## Done ##
popd
pause "Press Enter to exit..."