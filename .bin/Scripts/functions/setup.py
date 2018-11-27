# Wizard Kit: Functions - Setup

from functions.common import *
from functions.update import *

# STATIC VARIABLES
HKU =  winreg.HKEY_USERS
HKCR = winreg.HKEY_CLASSES_ROOT
HKCU = winreg.HKEY_CURRENT_USER
HKLM = winreg.HKEY_LOCAL_MACHINE
MOZILLA_FIREFOX_UBO_PATH = r'{}\{}\ublock_origin.xpi'.format(
    os.environ.get('PROGRAMFILES'),
    r'Mozilla Firefox\distribution\extensions')
OTHER_RESULTS = {
    'Error': {
        'CalledProcessError':   'Unknown Error',
        'FileNotFoundError':    'File not found',
    },
    'Warning': {}}
SETTINGS_CLASSIC_START = {
    r'Software\IvoSoft\ClassicShell\Settings': {},
    r'Software\IvoSoft\ClassicStartMenu': {
        'DWORD Items': {'ShowedStyle2': 1},
        },
    r'Software\IvoSoft\ClassicStartMenu\MRU': {},
    r'Software\IvoSoft\ClassicStartMenu\Settings': {
        'DWORD Items': {'SkipMetro': 1},
        'SZ Items': {
            'MenuStyle': 'Win7',
            'RecentPrograms': 'Recent',
            },
        },
    }
SETTINGS_EXPLORER_SYSTEM = {
    # Disable Location Tracking
    r'Software\Microsoft\Windows NT\CurrentVersion\Sensor\Overrides\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}': {
        'DWORD Items': {'SensorPermissionState': 0},
        },
    r'System\CurrentControlSet\Services\lfsvc\Service\Configuration': {
        'Status': {'Value': 0},
        },
    # Disable Telemetry
    r'Software\Microsoft\Windows\CurrentVersion\Policies\DataCollection': {
        'DWORD Items': {'AllowTelemetry': 0},
        },
    r'Software\Microsoft\Windows\CurrentVersion\Policies\DataCollection': {
        'DWORD Items': {'AllowTelemetry': 0},
        'WOW64_32': True,
        },
    r'Software\Policies\Microsoft\Windows\DataCollection': {
        'DWORD Items': {'AllowTelemetry': 0},
        },
    # Disable Wi-Fi Sense
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowWiFiHotSpotReporting': {
        'DWORD Items': {'Value': 0},
        },
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowAutoConnectToWiFiSenseHotspots': {
        'DWORD Items': {'Value': 0},
        },
    }
SETTINGS_EXPLORER_USER = {
    # Disable silently installed apps
    r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager': {
        'DWORD Items': {'SilentInstalledAppsEnabled': 0},
        },
    # Disable Tips and Tricks
    r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager': {
        'DWORD Items': {'SoftLandingEnabled ': 0},
        },
    # Hide People bar
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People': {
        'DWORD Items': {'PeopleBand': 0},
        },
    # Hide Search button / box
    r'Software\Microsoft\Windows\CurrentVersion\Search': {
        'DWORD Items': {'SearchboxTaskbarMode': 0},
        },
    # Change default Explorer view to "Computer"
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced': {
        'DWORD Items': {'LaunchTo': 1},
        },
    }
SETTINGS_GOOGLE_CHROME = {
    r'Software\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm': {
        'SZ Items': {
            'update_url': 'https://clients2.google.com/service/update2/crx'},
        'WOW64_32': True,
        },
    r'Software\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco': {
        'SZ Items': {
            'update_url': 'https://clients2.google.com/service/update2/crx'},
        'WOW64_32': True,
        },
    }
SETTINGS_MOZILLA_FIREFOX_32 = {
    r'Software\Mozilla\Firefox\Extensions': {
        'SZ Items': {
            'uBlock0@raymondhill.net': MOZILLA_FIREFOX_UBO_PATH},
        'WOW64_32': True,
        },
    }
SETTINGS_MOZILLA_FIREFOX_64 = {
    r'Software\Mozilla\Firefox\Extensions': {
        'SZ Items': {
            'uBlock0@raymondhill.net': MOZILLA_FIREFOX_UBO_PATH},
        },
    }
VCR_REDISTS = [
    {'Name': 'Visual C++ 2010 x32...',
        'Cmd': [r'2010sp1\x32\vcredist.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2010 x64...',
        'Cmd': [r'2010sp1\x64\vcredist.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2012 Update 4 x32...',
        'Cmd': [r'2012u4\x32\vcredist.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2012 Update 4 x64...',
        'Cmd': [r'2012u4\x64\vcredist.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2013 x32...',
        'Cmd': [r'2013\x32\vcredist.exe', '/install',
            '/passive', '/norestart']},
    {'Name': 'Visual C++ 2013 x64...',
        'Cmd': [r'2013\x64\vcredist.exe', '/install',
            '/passive', '/norestart']},
    {'Name': 'Visual C++ 2017 x32...',
        'Cmd': [r'2017\x32\vcredist.exe', '/install',
            '/passive', '/norestart']},
    {'Name': 'Visual C++ 2017 x64...',
        'Cmd': [r'2017\x64\vcredist.exe', '/install',
            '/passive', '/norestart']},
    ]

def config_classicstart():
    """Configure ClassicStart."""
    # User level, not system level
    cs_exe = r'{PROGRAMFILES}\Classic Shell\ClassicStartMenu.exe'.format(
        **global_vars['Env'])
    skin = r'{PROGRAMFILES}\Classic Shell\Skins\Metro-Win10-Black.skin7'.format(
        **global_vars['Env'])
    extract_item('ClassicStartSkin', silent=True)

    # Stop Classic Start
    run_program([cs_exe, '-exit'], check=False)
    sleep(1)
    kill_process('ClassicStartMenu.exe')

    # Configure
    write_registry_settings(SETTINGS_CLASSIC_START, all_users=False)
    if global_vars['OS']['Version'] == '10' and os.path.exists(skin):
        # Enable Win10 theme if on Win10
        key_path = r'Software\IvoSoft\ClassicStartMenu\Settings'
        with winreg.OpenKey(HKCU, key_path, access=winreg.KEY_WRITE) as key:
            winreg.SetValueEx(
                key, 'SkinW7', 0, winreg.REG_SZ, 'Metro-Win10-Black')
            winreg.SetValueEx(key, 'SkinVariationW7', 0, winreg.REG_SZ, '')

    # Pin Browser to Start Menu (Classic)
    firefox = r'{PROGRAMDATA}\Start Menu\Programs\Mozilla Firefox.lnk'.format(
        **global_vars['Env'])
    chrome = r'{PROGRAMDATA}\Start Menu\Programs\Google Chrome.lnk'.format(
        **global_vars['Env'])
    dest_path = r'{APPDATA}\ClassicShell\Pinned'.format(**global_vars['Env'])
    source = None
    dest = None
    if os.path.exists(firefox):
        source = firefox
        dest = r'{}\Mozilla Firefox.lnk'.format(dest_path)
    elif os.path.exists(chrome):
        source = chrome
        dest = r'{}\Google Chrome.lnk'.format(dest_path)
    if source:
        try:
            os.makedirs(dest_path, exist_ok=True)
            shutil.copy(source, dest)
        except Exception:
            pass # Meh, it's fine without

    # (Re)start Classic Start
    run_program([cs_exe, '-exit'], check=False)
    sleep(1)
    kill_process('ClassicStartMenu.exe')
    sleep(1)
    popen_program(cs_exe)

def config_explorer_system():
    """Configure Windows Explorer for all users via Registry settings."""
    write_registry_settings(SETTINGS_EXPLORER_SYSTEM, all_users=True)

def config_explorer_user():
    """Configure Windows Explorer for current user via Registry settings."""
    write_registry_settings(SETTINGS_EXPLORER_USER, all_users=False)

def disable_windows_telemetry():
    """Disable Windows 10 telemetry settings with O&O ShutUp10."""
    extract_item('ShutUp10', silent=True)
    cmd = [
        r'{BinDir}\ShutUp10\OOSU10.exe'.format(**global_vars),
        r'{BinDir}\ShutUp10\1201.cfg'.format(**global_vars),
        '/quiet']
    run_program(cmd)

def update_clock():
    """Set Timezone and sync clock."""
    run_program(['tzutil' ,'/s', WINDOWS_TIME_ZONE], check=False)
    run_program(['net', 'stop', 'w32ime'], check=False)
    run_program(
        ['w32tm', '/config', '/syncfromflags:manual',
            '/manualpeerlist:"us.pool.ntp.org time.nist.gov time.windows.com"',
            ],
        check=False)
    run_program(['net', 'start', 'w32ime'], check=False)
    run_program(['w32tm', '/resync', '/nowait'], check=False)

def write_registry_settings(settings, all_users=False):
    """Write registry values from custom dict of dicts."""
    hive = HKCU
    if all_users:
        hive = HKLM
    for k, v in settings.items():
        # CreateKey
        access = winreg.KEY_WRITE
        if 'WOW64_32' in v:
            access = access | winreg.KEY_WOW64_32KEY
        winreg.CreateKeyEx(hive, k, 0, access)

        # Create values
        with winreg.OpenKeyEx(hive, k, 0, access) as key:
            for name, value in v.get('DWORD Items', {}).items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            for name, value in v.get('SZ Items', {}).items():
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

# Installations
def install_adobe_reader():
    """Install Adobe Reader."""
    cmd = [
        r'{BaseDir}\Installers\Extras\Office\Adobe Reader DC.exe'.format(
            **global_vars),
        '/sAll',
        '/msi', '/norestart', '/quiet',
        'ALLUSERS=1',
        'EULA_ACCEPT=YES']
    run_program(cmd)

def install_chrome_extensions():
    """Update registry to install Google Chrome extensions for all users."""
    write_registry_settings(SETTINGS_GOOGLE_CHROME, all_users=True)

def install_classicstart_skin():
    """Extract ClassicStart skin to installation folder."""
    if global_vars['OS']['Version'] not in ('8', '8.1', '10'):
        raise UnsupportedOSError
    extract_item('ClassicStartSkin', silent=True)
    source = r'{BinDir}\ClassicStartSkin\Metro-Win10-Black.skin7'.format(
        **global_vars)
    dest_path = r'{PROGRAMFILES}\Classic Shell\Skins'.format(
        **global_vars['Env'])
    dest = r'{}\Metro-Win10-Black.skin7'.format(dest_path)
    os.makedirs(dest_path, exist_ok=True)
    shutil.copy(source, dest)

def install_firefox_extensions():
    """Update registry to install Firefox extensions for all users."""
    dist_path = r'{PROGRAMFILES}\Mozilla Firefox\distribution\extensions'.format(
        **global_vars['Env'])
    source_path = r'{CBinDir}\FirefoxExtensions.7z'.format(**global_vars)
    if not os.path.exists(source_path):
        raise FileNotFoundError

    # Update registry
    write_registry_settings(SETTINGS_MOZILLA_FIREFOX_32, all_users=True)
    write_registry_settings(SETTINGS_MOZILLA_FIREFOX_64, all_users=True)

    # Extract extension(s) to distribution folder
    cmd = [
        global_vars['Tools']['SevenZip'], 'e', '-aos', '-bso0', '-bse0',
        '-p{ArchivePassword}'.format(**global_vars),
        '-o{dist_path}'.format(dist_path=dist_path),
        source_path]
    run_program(cmd)

def install_ninite_bundle(mse=False):
    """Run Ninite file(s) based on OS version."""
    if global_vars['OS']['Version'] in ('8', '8.1', '10'):
        # Modern selection
        popen_program(r'{BaseDir}\Installers\Extras\Bundles\Modern.exe'.format(
            **global_vars))
    else:
        # Legacy selection
        if mse:
            cmd = r'{BaseDir}\Installers\Extras\Security'.format(**global_vars)
            cmd += r'\Microsoft Security Essentials.exe'
            popen_program(cmd)
        popen_program(r'{BaseDir}\Installers\Extras\Bundles\Legacy.exe'.format(
            **global_vars))

def install_vcredists():
    """Install all supported Visual C++ runtimes."""
    extract_item('_vcredists', silent=True)
    prev_dir = os.getcwd()
    try:
        os.chdir(r'{BinDir}\_vcredists'.format(**global_vars))
    except FileNotFoundError:
        # Ignored since the loop below will report the errors
        pass
    for vcr in VCR_REDISTS:
        try_and_print(message=vcr['Name'], function=run_program,
            cmd=vcr['Cmd'], other_results=OTHER_RESULTS)

    os.chdir(prev_dir)

# Misc
def open_device_manager():
    popen_program(['mmc', 'devmgmt.msc'])

def open_windows_activation():
    popen_program(['slui'])

def open_windows_updates():
    popen_program(['control', '/name', 'Microsoft.WindowsUpdate'])

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
