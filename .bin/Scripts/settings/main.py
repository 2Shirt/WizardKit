# Wizard Kit: Settings - Main / Branding

# Features
ENABLED_UPLOAD_DATA = False

# STATIC VARIABLES (also used by BASH and BATCH files)
## NOTE: There are no spaces around the = for easier parsing in BASH and BATCH
# Main Kit
ARCHIVE_PASSWORD='Abracadabra'
KIT_NAME_FULL='Wizard Kit'
KIT_NAME_SHORT='WK'
SUPPORT_MESSAGE='Please let 2Shirt know by opening an issue on GitHub'
# Live Linux
DIAG_SHARE='/srv/ClientInfo'
DIAG_USER='wkdiag'
MPRIME_LIMIT='7'                          # of minutes to run Prime95 during hw-diags
ROOT_PASSWORD='Abracadabra'
SKIP_UPLOAD='False'
TECH_PASSWORD='Abracadabra'
# Server IP addresses
DIAG_SERVER='10.0.0.10'
OFFICE_SERVER_IP='10.0.0.10'
QUICKBOOKS_SERVER_IP='10.0.0.10'
# Time Zones
LINUX_TIME_ZONE='America/Los_Angeles'     # See 'timedatectl list-timezones' for valid values
WINDOWS_TIME_ZONE='Pacific Standard Time' # See 'tzutil /l' for valid values
# WiFi
WIFI_SSID='SomeWifi'
WIFI_PASSWORD='Abracadabra'

# SERVER VARIABLES
## NOTE: Windows can only use one user per server. This means that if
##       one server serves multiple shares then you have to use the same
##       user/password for all of those shares.
BACKUP_SERVERS = [
    {   'IP':       '10.0.0.10',
        'Name':     'ServerOne',
        'Mounted':  False,
        'Share':    'Backups',
        'User':     'restore',
        'Pass':     'Abracadabra',
    },
    {   'IP':       '10.0.0.11',
        'Name':     'ServerTwo',
        'Mounted':  False,
        'Share':    'Backups',
        'User':     'restore',
        'Pass':     'Abracadabra',
    },
]
CLIENT_INFO_SERVER = {
    'IP':           '10.0.0.10',
    'RegEntry':     r'0x10001,0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
    'Share':        '/srv/ClientInfo',
    'User':         'upload',
}
CRASH_SERVER = {
    'Name':         'CrashServer',
    'Url':          '',
    'User':         '',
    'Pass':         '',
}
OFFICE_SERVER = {
    'IP':           OFFICE_SERVER_IP,
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Office',
    'User':         'restore',
    'Pass':         'Abracadabra',
}
QUICKBOOKS_SERVER = {
    'IP':           QUICKBOOKS_SERVER_IP,
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'QuickBooks',
    'User':         'restore',
    'Pass':         'Abracadabra',
}
WINDOWS_SERVER = {
    'IP':           '10.0.0.10',
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Windows',
    'User':         'restore',
    'Pass':         'Abracadabra',
}

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
