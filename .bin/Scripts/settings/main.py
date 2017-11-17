# Wizard Kit: Settings - Main / Branding

# Features
ENABLED_UPLOAD_DATA = False

# STATIC VARIABLES (also used by .cmd files)
## Not using spaces aroung '=' for easier .cmd substrings
ARCHIVE_PASSWORD='Abracadabra'
KIT_NAME_FULL='Wizard Kit'
KIT_NAME_SHORT='WK'
OFFICE_SERVER_IP='10.0.0.10'
QUICKBOOKS_SERVER_IP='10.0.0.10'
SUPPORT_TECH='2Shirt'
TIME_ZONE='Pacific Standard Time' # Always use "Standard Time" (DST is applied correctly)

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
    'RegEntry':     r'0x10001,0xcc674aebbd889f5fd553564adcf3cab550791eca12542033d52134db893c95aabb6b318a4621d8116f6838d873edfe9db4509e1dfc9177ee7484808a62cbc42b913387f694fd67e81950f85198acf721c5767b54db7b864d69cce65e12c78c87d0fb4fc54996609c9b9274b1de7bae2f95000c9ca8d7e3f9b3f2cdb21cd578adf9ba98d10400a8203bb1a879a4cd2fad99baeb12738b9b4b99fec821f881acb62598a43c059f74af287bc8dceeb4821317aa44e2e0ee66d346927a654c702854a71a2eaed6a53f6be9360c7049974a2597a548361da42ac982ae55f993700a8b1fc9f3b4458314fbd41f239de0a29716cdcefbbb2c8d02b4c2effa4163cfeac9',
    'Share':        '/srv/ClientInfo',
    'User':         'upload',
}
QUICKBOOKS_SERVER = {
    'IP':           QUICKBOOKS_SERVER_IP,
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'QuickBooks',
    'User':         'restore',
    'Pass':         'Abracadabra',
}
OFFICE_SERVER = {
    'IP':           OFFICE_SERVER_IP,
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Office',
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
