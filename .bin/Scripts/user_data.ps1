# Wizard Kit: List the data usage for the current user (and other users when possible)

param([string]$log)

cd $(Split-Path $MyInvocation.MyCommand.Path)
. .\init.ps1

#Folder GUIDs from: https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx
$user_dirs = , ("Desktop", "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")
$user_dirs += , ("Documents", "Personal", "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}")
$user_dirs += , ("Downloads", "{374DE290-123F-4565-9164-39C4925E467B}")
$user_dirs += , ("Favorites", "{1777F761-68AD-4D8A-87BD-30B759FA33DD}")
$user_dirs += , ("Music", "My Music", "{4BD8D571-6D19-48D3-BE97-422220080E43}")
$user_dirs += , ("Pictures", "My Pictures", "{33E28130-4E1E-4676-835A-98395C3BC3BB}")
$user_dirs += , ("Videos", "My Video", "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}")
#=SkyDrive=
#=Dropbox=

function print-dir-size ($name, $location) {
    #"{0}: {1}" -f $name, $location
    $name += ":"
    $results = .\Get-FolderSize.ps1 "$location"
    [int64]$bytes = $results.TotalBytes
    if ($bytes -ge 1073741824) {
        $total = "{0:N2}" -f [single]$results.TotalGBytes
        $s = "    {0} {1} Gb ({2})" -f $name.PadRight(10), $total.PadLeft(10), $location
    } elseif ($bytes -ge 1048576) {
        $total = "{0:N2}" -f [single]$results.TotalMBytes
        $s = "    {0} {1} Mb ({2})" -f $name.PadRight(10), $total.PadLeft(10), $location
    } elseif ($bytes -ge 1024) {
        $total = "{0:N2}" -f [single]($bytes/1024)
        $s = "    {0} {1} Kb ({2})" -f $name.PadRight(10), $total.PadLeft(10), $location
    } else {
        $total = "{0:N0}" -f $bytes
        $s = "    {0} {1} Bytes ({2})" -f $name.PadRight(10), $total.PadLeft(7), $location
    }
    WK-write "$s" "$log"
}

foreach ($user in get-wmiobject -class win32_useraccount) {
    if (test-path registry::hku\$($user.sid)) {
        WK-write ("  User: {0}" -f $user.name) "$log"
        
        # Profile
        $user_profile = gp "registry::hklm\software\microsoft\windows nt\currentversion\profilelist\$($user.sid)"
        print-dir-size "Profile" $user_profile.ProfileImagePath
        WK-write "    ------------------------" "$log"
        
        # Shell Folders
        $shell_folders = gp "registry::hku\$($user.sid)\software\microsoft\windows\currentversion\explorer\shell folders"
        foreach ($dir in $user_dirs) {
            $dir_name = $dir[0]
            foreach ($reg_name in $dir) {
                $dir_location = $shell_folders.$reg_name
                if ($dir_location -and $(test-path "$dir_location")) {
                    print-dir-size $dir_name $dir_location
                    break
                }
            }
        }
        
        # Online Backups
        foreach ($dir in "Dropbox", "Mozy", "OneDrive", "SkyDrive") {
            $spacer = "True"
            $dir_name = $dir
            $dir_location = "{0}\{1}" -f $user_profile.ProfileImagePath, $dir
            if (test-path $dir_location) {
                if ($spacer) {
                    "    ------------------------"
                    rv spacer
                }
                print-dir-size $dir_name $dir_location
            }
        }
        
        # Spacer
        WK-write "" "$log"
    }
}