# WK-BrowserReset

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1
clear
$host.UI.RawUI.WindowTitle = "WK Browser Reset Tool"
$backup_path = "$WKPath\Backups\$username\$date"
$logpath = "$WKPath\Info\$date"
md "$backup_path" 2>&1 | out-null
md "$logpath" 2>&1 | out-null
$log = "$logpath\Browsers.log"
$bin = (Get-Item $wd).Parent.FullName

# Vars
$ff_appdata = "$appdata\Mozilla\Firefox"
$ff_clean = $false
$ff_exe = "$programfiles86\Mozilla Firefox\firefox.exe"
if (test-path "$programfiles\Mozilla Firefox\firefox.exe") {
    $ff_exe = "$programfiles\Mozilla Firefox\firefox.exe"
}
$ff_profile_list = @(gci "$ff_appdata\Profiles" 2> $null | ?{ $_.PSIsContainer })
$ff_profile_list = $ff_profile_list -inotmatch '\.wkbak$'
$chrome_appdata = "$localappdata\Google\Chrome"
$chrome_clean = $false
$chrome_exe = "$programfiles86\Google\Chrome\Application\chrome.exe"
$chrome_profile_list = @(gci "$chrome_appdata\User Data" 2> $null | ?{ $_.PSIsContainer })
$chrome_profile_list = $chrome_profile_list -inotmatch '\.wkbak$' -imatch '^(Default|Profile)'

# OS Check
. .\os_check.ps1

# Functions
function gen-backup-name {
    param ([String]$name)
    
    # Add .wkbak to name
    $newname = "$name.wkbak"
    
    # Check if the new name exists
    if (test-path "$newname") {
        # Change name to avoid overwriting any backups
        $x = 2
        $newname = "$name.wkbak$x"
        while (test-path "$newname") {
            $x += 1
            $newname = "$name.wkbak$x"
        }
    }
    
    return $newname
}
function ff-create-default-profile {
    wk-write "  Creating new default profile" "$log"
    # Check for existing profiles
    if ($ff_profile_list.length -gt 0) {
        wk-error "  Firefox profile folders found. Possibly corrupt?" "$log"
        return $false
    }

    # Backup profiles.ini if necessary
    ## NOTE: While you can use the profiles.ini to recreate the default profile,
    ##       it is better to create a new ini to better ensure the profile dir
    ##       will be in "$ff_appdata\Profiles\"
    if (test-path "$ff_appdata\profiles.ini") {
        mv "$ff_appdata\profiles.ini" (gen-backup-name "$ff_appdata\profiles.ini")
    }

    # Create default profile
    if (test-path "$ff_exe") {
        $ff_args = @(
            "-createprofile",
            "default")
        start -wait "$ff_exe" -argumentlist $ff_args -windowstyle minimized
    } else {
        wk-error "  firefox.exe not found. Please verify installation." "$log"
        return $false
    }
    return $true
}


## Internet Explorer ##
wk-write "==== Internet Explorer ====" "$log"

# Cleanup
if (test-path ".bin\Bleachbit") {
    wk-write "  Removing temporary files" "$log"
    pushd ".bin\Bleachbit"
    start -wait "bleachbit_console.exe" -argumentlist @("-c", "internet_explorer.forms", "internet_explorer.temporary_files", "winapp2_internet.internet_explorer_10_11") -verb runas -windowstyle minimized
    popd
}

# Backup Favorites
if (test-path "$userprofile\Favorites") {
    wk-write "  Backing up Favorites" "$log"
    pushd "$userprofile"
    $sz_args = @(
        "a",
        "-t7z",
        "-mx=1",
        "$backup_path\IE Favorites.7z",
        "Favorites")
    start "$bin\7-Zip\7z.exe" -argumentlist $sz_args -wait -windowstyle minimized
    popd
}

# Get IE settings
$reset_homepage = $true
$ie_settings = gp -path hkcu:"Software\Microsoft\Internet Explorer\Main"

# Reset IE settings (argmuentlist is case sensitive)
if (ask "  Reset to default settings?" "$log") {
    start -wait rundll32.exe -argumentlist 'inetcpl.cpl,ResetIEtoDefaults'
}

# Get homepage(s)
$_current_homepage = $ie_settings."Start Page"
if ($_current_homepage -ne $null -and $_current_homepage.Length -ne 0) {
    $_secondary_homepages = @($ie_settings."Secondary Start Pages")
    wk-write "  Current homepage: $_current_homepage" "$log"
    foreach ($p in $_secondary_homepages) {
        if ($p -ne $null -and $p.Length -ne 0) {
            wk-write "                    $p" "$log"
        }
    }
    if ($_current_homepage -inotmatch '^https://www\.google\.com/$' -or $_secondary_homepages -imatch '^.+') {
        $reset_homepage = (ask "  Replace current homepage with google.com?" "$log")
    }
}

# Set homepage(s)
wk-write "  Setting homepage" "$log"
if ($reset_homepage) {
    sp -path hkcu:"Software\Microsoft\Internet Explorer\Main" -name "Start Page" -Value "https://www.google.com/" 2>&1 | out-null
    rp -path hkcu:"Software\Microsoft\Internet Explorer\Main" -name "Secondary Start Pages" 2>&1 | out-null
} else {
    sp -path hkcu:"Software\Microsoft\Internet Explorer\Main" -name "Start Page" -Value $_current_homepage 2>&1 | out-null
    new-itemproperty -path hkcu:"Software\Microsoft\Internet Explorer\Main" -name "Secondary Start Pages" -propertytype MultiString -value $_secondary_homepages 2>&1 | out-null
}

# Additional settings
if (test-path "$programfiles86\Internet Explorer\iexplore.exe") {
    if (ask "  Install Google search add-on?" "$log") {
        start -wait "$programfiles86\Internet Explorer\iexplore.exe" -argumentlist "http://www.iegallery.com/en-us/Addons/Details/813"
    }
    #if (ask "  Install AdBlock Plus?" "$log") {
    #    start -wait "$programfiles86\Internet Explorer\iexplore.exe" -argumentlist "https://adblockplus.org"
    #}
} else {
    wk-error "  $programfiles86\Internet Explorer\iexplore.exe not found" "$log"
}
wk-write "" "$log"
pause


## Mozilla Firefox ##
wk-write "==== Mozilla Firefox ====" "$log"
$ff_errors = 0

# Reduce size of AppData folder
if (test-path ".bin\Bleachbit") {
    wk-write "  Removing temporary files" "$log"
    pushd ".bin\Bleachbit"
    start -wait "bleachbit_console.exe" -argumentlist @("-c", "firefox.cache", "firefox.forms", "firefox.session_restore", "firefox.vacuum", "winapp2_mozilla.corrupt_sqlites") -verb runas -nonewwindow
    popd
}

# Backup AppData
if (test-path "$ff_appdata") {
    wk-write "  Backing up AppData" "$log"
    pushd "$ff_appdata"
    $sz_args = @(
        "a",
        "-t7z",
        "-mx=1",
        "$backup_path\Firefox.7z",
        "Profiles",
        "profiles.ini")
    start "$bin\7-Zip\7z.exe" -argumentlist $sz_args -wait -windowstyle minimized
    popd
}

# Create default profile if necessary
if ($ff_profile_list.length -eq 0) {
    if (ff-create-default-profile) {
        # Update profile list to catch newly created profiles
        sleep -s 1
        $ff_profile_list = @(gci "$ff_appdata\Profiles" 2> $null | ?{ $_.PSIsContainer })
        $ff_profile_list = $ff_profile_list -inotmatch '\.wkbak\d*$'
        if ($ff_profile_list.length -eq 0) {
            wk-warn "  Failed to create default profile." "$log"
            $ff_errors += 1
        } else {
            # Configure new profile
            $ff_clean = $true
        }
    } else {
        wk-error "  Failed to create default profile." "$log"
        $ff_errors += 1
    }
} else {
    wk-write "  Profiles found: $($ff_profile_list.length)" "$log"
    $ff_clean = (ask "  Reset profile(s) to safe settings?" "$log")
}

# Reset profile(s) to safe defaults
if ($ff_clean -and $ff_errors -eq 0) {
    pushd "$ff_appdata\Profiles"
    foreach ($ff_profile in $ff_profile_list) {
        wk-write "  Resetting profile: $ff_profile" "$log"

        # Backup old settings and only preserve essential settings
        $ff_profile_bak = (gen-backup-name "$ff_profile")
        mv "$ff_profile" "$ff_profile_bak"
        md "$ff_profile" 2>&1 | out-null
        
        # Add "search.json" to $robocopy_args preserve added search engines
        $robocopy_args = @(
            "/r:3",
            "/w:1",
            "$ff_profile_bak",
            "$ff_profile",
            "cookies.sqlite",
            "formhistory.sqlite",
            "key3.db",
            "logins.json",
            "persdict.dat",
            "places.sqlite")
        start "robocopy" -argumentlist $robocopy_args -wait -windowstyle minimized
        
        # Add "searchplugins" below to preserve added search engines
        foreach ($subdir in @("bookmarkbackups")) {
            if (test-path "$ff_profile_bak\$subdir") {
                md "$ff_profile\$subdir" 2>&1 | out-null
                $robocopy_args = @(
                    "/e",
                    "/r:3",
                    "/w:1",
                    "$ff_profile_bak\$subdir",
                    "$ff_profile\$subdir")
                start "robocopy" -argumentlist $robocopy_args -wait -windowstyle minimized
            }
        }

        # Set homepage and search settings
        wk-write "    Setting homepage and default search" "$log"
        out-file -encoding 'ascii' -filepath "$ff_profile\prefs.js" -inputobject 'user_pref("browser.search.geoSpecificDefaults", false);'
        out-file -encoding 'ascii' -filepath "$ff_profile\prefs.js" -inputobject 'user_pref("browser.search.defaultenginename", "Google");' -append
        out-file -encoding 'ascii' -filepath "$ff_profile\prefs.js" -inputobject 'user_pref("browser.search.defaultenginename.US", "Google");' -append
        $homepage = "https://www.google.com/"
        if (test-path "$ff_profile_bak\prefs.js") {
            $_prefs = gc "$ff_profile_bak\prefs.js"
            if ($_prefs -imatch '"browser.startup.homepage"') {
                $_current_homepage = $_prefs -imatch '"browser.startup.homepage"'
                $_current_homepage = $_current_homepage -ireplace 'user_pref\("browser.startup.homepage", "(.*)"\);', '$1'
                $_header = "    Current homepage:"
                foreach ($url in  @("$_current_homepage".split("|"))) {
                    wk-write "$_header $_current_homepage" "$log"
                    $_header = "                     "
                }
                if ($_current_homepage -inotmatch '^https://www\.google\.com/$') {
                    if (!(ask "    Replace current homepage with google.com?" "$log")) {
                        $homepage = $_cur_home
                    }
                }
            }
        }
        $homepage = 'user_pref("browser.startup.homepage", "' + $homepage + '");'
        out-file -encoding 'ascii' -filepath "$ff_profile\prefs.js" -inputobject $homepage -append
        wk-write "" "$log"
    }
    popd
}

# Install uBlock Origin
if (test-path "$ff_exe") {
    if ($ff_errors -eq 0 -and (ask "  Install uBlock Origin?" "$log")) {
        start -wait "$ff_exe" -argumentlist "https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/"
    }
} else {
    wk-error "  firefox.exe not found. Please verify installation." "$log"
}

wk-write "" "$log"
pause


## Google Chrome ##
wk-write "==== Google Chrome ====" "$log"
$chrome_errors = 0

# Reduce size of AppData folder
if (test-path ".bin\Bleachbit") {
    wk-write "  Removing temporary files" "$log"
    pushd ".bin\Bleachbit"
    start -wait "bleachbit_console.exe" -argumentlist @("-c", "google_chrome.cache", "google_chrome.form_history", "google_chrome.search_engines", "google_chrome.session", "google_chrome.vacuum") -verb runas -nonewwindow
    popd
}

# Backup AppData
if (test-path "$chrome_appdata") {
    wk-write "  Backing up AppData" "$log"
    pushd "$chrome_appdata"
    $sz_args = @(
        "a",
        "-t7z",
        "-mx=1",
        "$backup_path\Chrome.7z",
        '"User Data"')
    start "$bin\7-Zip\7z.exe" -argumentlist $sz_args -wait -windowstyle minimized
    popd
}

# Check for profiles
if ($chrome_profile_list.length -gt 0) {
    wk-write "  Profiles found: $($chrome_profile_list.length)" "$log"
    $chrome_clean = (ask "  Reset profile(s) to safe settings?" "$log")
} else {
    wk-warn "  No profiles found" "$log"
}

# Reset profile(s) to safe defaults
if ($chrome_clean -and $chrome_errors -eq 0) {
    pushd "$chrome_appdata\User Data"
    foreach ($chrome_profile in $chrome_profile_list) {
        wk-write "  Cleaning profile: $chrome_profile" "$log"
        $chrome_profile_bak = (gen-backup-name "$chrome_profile")
        mv "$chrome_profile" "$chrome_profile_bak"
        md "$chrome_profile" 2>&1 | out-null
        $robocopy_args = @(
            "/r:3",
            "/w:1",
            "$chrome_profile_bak",
            "$chrome_profile",
            "Bookmarks",
            "Cookies",
            "Favicons",
            '"Google Profile*"',
            "History",
            '"Login Data"',
            '"Top Sites"',
            "TransportSecurity",
            '"Visited Links"',
            '"Web Data"')
        start "robocopy" -argumentlist $robocopy_args -wait -windowstyle minimized
        wk-write "" "$log"
    }
    popd
}

# Test for single-user installation
if (test-path "$chrome_appdata\Application\chrome.exe") {
    if (test-path "$chrome_exe") {
        wk-warn "  Single-user and multi-user installations present. Please reinstall Chrome." "$log"
    } else {
        $chrome_exe = "$chrome_appdata\Application\chrome.exe"
    }
}

if (test-path "$chrome_exe") {
    # Set Chrome as default browser
    start -wait "$chrome_exe" -argumentlist "--make-default-browser"
    
    # Install uBlock Origin
    if ($chrome_errors -eq 0 -and (ask "  Install uBlock Origin?" "$log")) {
        start -wait "$chrome_exe" -argumentlist "https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en"
    }
} else {
    wk-error "  chrome.exe not found. Please verify installation." "$log"
}
wk-write "" "$log"


## Done ##
popd
pause "Press Enter to exit..."

# Open log
$notepad2 = "$bin\Notepad2\Notepad2-Mod.exe"
if (test-path $notepad2) {
    start "$notepad2" -argumentlist $log
} else {
    start "notepad" -argumentlist $log
}
