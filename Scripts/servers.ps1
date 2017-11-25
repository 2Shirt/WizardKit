# WK server functions

## Init ##
$wd = $(Split-Path $MyInvocation.MyCommand.Path)
pushd "$wd"
. .\init.ps1

# Variables
$source_server = "10.0.0.10"
$backup_servers = @(
    @{  "ip"="10.0.0.10";
        "letter"="Z";
        "name"="ServerOne";
        "path"="Backups"},
    @{  "ip"="10.0.0.11";
        "name"="ServerTwo";
        "letter"="Y";
        "path"="Backups"}
    )
$backup_user = "backup"
$backup_pass = "Abracadabra"

# Functions
function select-server {
    # Check for available servers
    $avail_servers = @(Get-PSDrive | Where-Object {$_.DisplayRoot -imatch '\\\\'})
    if ($avail_servers.count -eq 0) {
        wk-error "No suitable backup servers were detected."
        return $false
    }
    
    # Build menu and get selection
    $selection = $null
    $main_set = @()
    foreach ($server in $avail_servers) {
        $_entry = "{0} ({1} free)" -f $server.Description, (human-size $server.Free)
        $main_set += @{Name=$_entry}
    }
    $actions = @(@{Name="Main Menu"; Letter="M"})
    $selection = (menu-select "Where are we saving the backup image(s)?" $main_set $actions)
    
    if ($selection -imatch '^\d+$') {
        $selection -= 1
        return $avail_servers[$selection]
    }
    return $selection
}
function mount-servers {
    # Mount servers
    wk-write "Connecting to backup server(s)"
    foreach ($_server in $backup_servers) {
        if (test-connection $_server.ip -count 3 -quiet) {
            try {
                $_path = "\\{0}\{1}" -f $_server.ip, $_server.path
                $_drive = "{0}:" -f $_server.letter
                net use $_drive "$_path" /user:$backup_user $backup_pass | Out-Null
                wk-write ("`t{0} server: mounted" -f $_server.name)
                
                # Add friendly description
                $_regex = "^{0}$" -f $_server.letter
                (Get-PSDrive | Where-Object {$_.Name -imatch $_regex}).Description = $_server.name
            } catch {
                wk-warn ("`t{0} server: failed" -f $_server.name)
            }
        } else {
            wk-warn ("`t{0} server: timed-out" -f $_server.name)
        }
    }
}
function unmount-servers {
    # Unmount servers
    wk-write "Disconnecting from backup server(s)"
    $mounted_servers = @(Get-PSDrive | Where-Object {$_.DisplayRoot -imatch '\\\\'})
    foreach ($_server in $mounted_servers) {
        try {
            $_drive = "{0}:" -f $_server.Name
            net use $_drive /delete | Out-Null
            #wk-warn ("`t{0} server: unmounted" -f $_server.name)
            wk-warn "`tServer: unmounted"
        } catch {
            #wk-warn ("`t{0} server: failed" -f $_server.name)
            wk-warn "`tServer: failed"
        }
    }
}
