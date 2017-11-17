# Wizard Kit: Browser Reset Tool

import os
import re
import shutil
import subprocess
import winreg

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Browser Reset Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['BackupDir'] = '{ClientDir}\\Backups\\{Date}\\{USERNAME}'.format(**vars_wk, **vars_wk['Env'])
vars_wk['LogFile'] = '{LogDir}\\Reset Browsers.log'.format(**vars_wk)
vars_wk['BleachBit'] = '{BinDir}\\BleachBit\\bleachbit_console.exe'.format(**vars_wk)
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
vars_wk['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('.exe', '64.exe')
    vars_wk['SevenZip'] = vars_wk['SevenZip'].replace('.exe', '64.exe')
os.makedirs('{BackupDir}'.format(**vars_wk), exist_ok=True)
os.makedirs('{LogDir}'.format(**vars_wk), exist_ok=True)
os.makedirs('{TmpDir}'.format(**vars_wk), exist_ok=True)

# VARIABLES
DEFAULT_HOMEPAGE = 'https://www.google.com/'
REGEX_CHROMIUM_ITEMS = re.compile(r'^(Bookmarks|Cookies|Favicons|Google Profile|History|Login Data|Top Sites|TransportSecurity|Visited Links|Web Data).*', re.IGNORECASE)
REGEX_FIREFOX = re.compile(r'^(bookmarkbackups|(cookies|formhistory|places).sqlite|key3.db|logins.json|persdict.dat)$', re.IGNORECASE)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

def backup_browsers():
    """Create backups of all supported browsers in the BackupDir."""
    print_info('* Backing up browser data', vars_wk['LogFile'])
    # Chromium
    if os.path.exists('{LOCALAPPDATA}\\Chromium\\User Data'.format(**vars_wk['Env'])):
        print_standard('  Chromium', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Chromium.7z" "{LOCALAPPDATA}\\Chromium\\User Data"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Google Chrome
    if os.path.exists('{LOCALAPPDATA}\\Google\\Chrome\\User Data'.format(**vars_wk['Env'])):
        print_standard('  Google Chrome', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Google Chrome.7z" "{LOCALAPPDATA}\\Google\\Chrome\\User Data"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Google Chrome Canary
    if os.path.exists('{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data'.format(**vars_wk['Env'])):
        print_standard('  Google Chrome Canary', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Google Chrome Canary.7z" "{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Internet Explorer
    if os.path.exists('{USERPROFILE}\\Favorites'.format(**vars_wk['Env'])):
        print_standard('  Internet Explorer', vars_wk['LogFile'])
        _cmd = [
            vars_wk['SevenZip'],
            'a',
            '-aoa',
            '-bso0',
            '-bse0',
            '-mx=1',
            '{BackupDir}\\Internet Explorer.7z'.format(**vars_wk),
            '{USERPROFILE}\\Favorites'.format(**vars_wk['Env'])]
        run_program(_cmd, check=False, pipe=False)
        run_program('reg export "hkcu\\Software\\Microsoft\\Internet Explorer" "{TmpDir}\\Internet Explorer (HKCU).reg" /y'.format(**vars_wk), check=False, shell=True)
        run_program('reg export "hklm\\Software\\Microsoft\\Internet Explorer" "{TmpDir}\\Internet Explorer (HKLM).reg" /y'.format(**vars_wk), check=False, shell=True)
        _cmd = [
            vars_wk['SevenZip'],
            'a',
            '-aoa',
            '-bso0',
            '-bse0',
            '-mx=1',
            '{BackupDir}\\Internet Explorer.7z'.format(**vars_wk),
            '{TmpDir}\\Internet*.reg'.format(**vars_wk)]
        run_program(_cmd, check=False, pipe=False)
    
    # Mozilla Firefox
    if os.path.exists('{APPDATA}\\Mozilla\\Firefox'.format(**vars_wk['Env'])):
        print_standard('  Mozilla Firefox', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Mozilla Firefox.7z" "{APPDATA}\\Mozilla\\Firefox\\Profile*"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Opera
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Stable'.format(**vars_wk['Env'])):
        print_standard('  Opera', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Opera.7z" "{APPDATA}\\Opera Software\\Opera Stable"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Opera Beta
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Next'.format(**vars_wk['Env'])):
        print_standard('  Opera Beta', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Opera Beta.7z" "{APPDATA}\\Opera Software\\Opera Next"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    
    # Opera Dev
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Developer'.format(**vars_wk['Env'])):
        print_standard('  Opera Dev', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Opera Dev.7z" "{APPDATA}\\Opera Software\\Opera Developer"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)

def clean_chromium_profile(profile):
    """Renames profile folder as backup and then recreates the folder with only the essential files."""
    print_info('    Resetting profile: {name}'.format(name=profile.name), vars_wk['LogFile'])
    backup_path = rename_as_backup(profile.path)
    os.makedirs(profile.path, exist_ok=True)
    
    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_CHROMIUM_ITEMS.search(entry.name):
            shutil.copy(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))

def clean_firefox_profile(profile):
    """Renames profile folder as backup and then recreates the folder with only the essential files."""
    print_info('    Resetting profile: {name}'.format(name=profile.name), vars_wk['LogFile'])
    backup_path = rename_as_backup(profile.path)
    homepages = []
    os.makedirs(profile.path, exist_ok=True)
    
    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_FIREFOX.search(entry.name):
            if entry.is_dir():
                shutil.copytree(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))
            else:
                shutil.copy(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))
    
    # Check current Homepage
    try:
        with open('{path}\\prefs.js'.format(path=backup_path), 'r') as f:
            _search = re.search(r'browser\.startup\.homepage", "([^"]*)"', f.read(), re.IGNORECASE)
            if _search:
                homepages = _search.group(1).split('|')
    except FileNotFoundError:
        pass
    
    # Set profile defaults
    with open('{path}\\prefs.js'.format(path=profile.path), 'a', encoding='ascii') as f:
        f.write('user_pref("browser.search.geoSpecificDefaults", false);\n')
        
        # Set search to Google
        f.write('user_pref("browser.search.defaultenginename", "Google");\n')
        f.write('user_pref("browser.search.defaultenginename.US", "Google");\n')
        
        # Set homepage
        if len(homepages) == 0:
            homepages = [DEFAULT_HOMEPAGE]
        elif len(homepages) > 1 or DEFAULT_HOMEPAGE not in homepages:
            # Not set to [DEFAULT_HOMEPAGE], ask if switching
            print_warning('    Current homepage: {url}'.format(url=homepages[0]), vars_wk['LogFile'])
            for url in homepages[1:]:
                print_warning('                    : {url}'.format(url=url), vars_wk['LogFile'])
            if ask('    Replace with {url}?'.format(url=DEFAULT_HOMEPAGE), vars_wk['LogFile']):
                homepages = [DEFAULT_HOMEPAGE]
        f.write('user_pref("browser.startup.homepage", "{urls}");\n'.format(urls='|'.join(homepages)))

def clean_internet_explorer():
    """Uses the built-in function to reset IE and sets the homepage."""
    print_info('    Closing any open windows', vars_wk['LogFile'])
    kill_process('iexplore.exe')
    print_info('    Resetting internet options', vars_wk['LogFile'])
    run_program('rundll32.exe', ['inetcpl.cpl,ResetIEtoDefaults'], check=False)
    
    # Set homepage
    key = r'Software\Microsoft\Internet Explorer\Main'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as _key:
        homepage = winreg.QueryValueEx(_key, 'Start Page')[0]
        try:
            secondary_homepages = winreg.QueryValueEx(_key, 'Secondary Start Pages')[0]
        except FileNotFoundError:
            secondary_homepages = []
    print_standard('    Current homepage: ' + homepage, vars_wk['LogFile'])
    for page in secondary_homepages:
        print_standard('                    : ' + page, vars_wk['LogFile'])
    if homepage != DEFAULT_HOMEPAGE or len(secondary_homepages) > 0:
        if ask('    Replace current homepage with google.com?', vars_wk['LogFile']):
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, access=winreg.KEY_WRITE) as _key:
                winreg.SetValueEx(_key, 'Start Page', 0, winreg.REG_SZ, DEFAULT_HOMEPAGE)
                try:
                    winreg.DeleteValue(_key, 'Secondary Start Pages')
                except FileNotFoundError:
                    pass

def exit_script():
    # pause("Press Enter to exit...")
    quit()

def get_chrome_exe():
    """Check for conflicting Chrome installations and return chrome.exe path as str."""
    install_multi = '{PROGRAMFILES}\\Google\\Chrome\\Application\\chrome.exe'.format(**vars_wk['Env'])
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        install_multi = '{PROGRAMFILES(X86)}\\Google\\Chrome\\Application\\chrome.exe'.format(**vars_wk['Env'])
    install_single = '{LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe'.format(**vars_wk['Env'])
    if os.path.exists(install_multi):
        if os.path.exists(install_single):
            print_warning('    WARNING: Single-user and multi-user installations present.', vars_wk['LogFile'])
            print_warning('             It is recommended to move to only having the multi-user installation.', vars_wk['LogFile'])
        return install_multi
    elif os.path.exists(install_single):
        return install_single
    else:
        print_error('    ERROR: chrome.exe not found. Please verify installation.', vars_wk['LogFile'])
        return None

def get_chrome_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{LOCALAPPDATA}\\Google\\Chrome\\User Data'.format(**vars_wk['Env'])):
        if entry.is_dir() and re.search(r'^(Default|Profile)', entry.name, re.IGNORECASE):
            profiles.append(entry)
    profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    
    return profiles

def get_chrome_canary_exe():
    """Check for Google Chrome Canary installation and return chrome.exe path as str."""
    prog_exe = '{LOCALAPPDATA}\\Google\\Chrome SxS\\Application\\chrome.exe'.format(**vars_wk['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        print_error('    ERROR: chrome.exe not found. Please verify installation.', vars_wk['LogFile'])
        return None

def get_chrome_canary_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data'.format(**vars_wk['Env'])):
        if entry.is_dir() and re.search(r'^(Default|Profile)', entry.name, re.IGNORECASE):
            profiles.append(entry)
    profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    
    return profiles

def get_iexplorer_exe():
    """Find and return iexplorer.exe path as str."""
    ie_exe = '{PROGRAMFILES}\\Internet Explorer\\iexplore.exe'.format(**vars_wk['Env'])
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        ie_exe = '{PROGRAMFILES(X86)}\\Internet Explorer\\iexplore.exe'.format(**vars_wk['Env'])
    return ie_exe

def get_firefox_exe():
    """Check for Mozilla Firefox installation and return firefox.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Mozilla Firefox\\firefox.exe'.format(**vars_wk['Env'])
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Mozilla Firefox\\firefox.exe'.format(**vars_wk['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_firefox_dev_exe():
    """Check for Mozilla Firefox Developer Edition installation and return firefox.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Firefox Developer Edition\\firefox.exe'.format(**vars_wk['Env'])
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Firefox Developer Edition\\firefox.exe'.format(**vars_wk['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_exe():
    """Check for Opera installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera\\launcher.exe'.format(**vars_wk['Env'])
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Opera\\launcher.exe'.format(**vars_wk['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_firefox_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{APPDATA}\\Mozilla\\Firefox\\Profiles'.format(**vars_wk['Env'])):
        if entry.is_dir():
            profiles.append(entry)
    profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    
    return profiles

def create_firefox_default_profiles():
    """Create new default profile for Mozilla Firefox for both stable and dev releases."""
    print_warning('    WARNING: Creating new default profile.', vars_wk['LogFile'])
    firefox_exe = get_firefox_exe()
    firefox_dev_exe = get_firefox_dev_exe()
    profiles_ini_path = '{APPDATA}\\Mozilla\\Firefox\\profiles.ini'.format(**vars_wk['Env'])
    
    # Rename profiles.ini
    if os.path.exists(profiles_ini_path):
        rename_as_backup(profiles_ini_path)
    
    # Create profile(s)
    if firefox_exe is not None:
        run_program(firefox_exe, ['-createprofile', 'default'], check=False)
    if firefox_dev_exe is not None:
        run_program(firefox_dev_exe, ['-createprofile'], check=False)

def get_opera_beta_exe():
    """Check for Opera Beta installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera beta\\launcher.exe'.format(**vars_wk['Env'])
    # Installs as 64-bit on a 64-bit OS so PROGRAMFILES should always be correct
    
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_dev_exe():
    """Check for Opera Beta installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera developer\\launcher.exe'.format(**vars_wk['Env'])
    # Installs as 64-bit on a 64-bit OS so PROGRAMFILES should always be correct
    
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_profile():
    """Find an existing Opera profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{APPDATA}\\Opera Software'.format(**vars_wk['Env'])):
        if entry.is_dir() and entry.name == 'Opera Stable':
            return [entry]
    
    return profiles

def get_opera_beta_profile():
    """Find an existing Opera Beta profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{APPDATA}\\Opera Software'.format(**vars_wk['Env'])):
        if entry.is_dir() and entry.name == 'Opera Next':
            return [entry]
    
    return profiles

def get_opera_dev_profile():
    """Find an existing Opera Dev profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    for entry in os.scandir('{APPDATA}\\Opera Software'.format(**vars_wk['Env'])):
        if entry.is_dir() and entry.name == 'Opera Developer':
            return [entry]
    
    return profiles

def remove_temp_files():
    """Run BleachBit to delete cache, temp, and corrupt data from browsers."""
    print_info('* Deleting browser temp data', vars_wk['LogFile'])
    if not ask('  Proceed?', vars_wk['LogFile']):
        # Bail early
        return
    # Extract and delete
    extract_item('BleachBit', vars_wk, silent=True)
    _args = [
        '-c',
        # Chromium
        'chromium.cache',
        'chromium.search_engines',
        'chromium.current_session',
        'chromium.vacuum',
        # Google Chrome
        'google_chrome.cache',
        'google_chrome.search_engines',
        'google_chrome.session',
        'google_chrome.vacuum',
        # Internet Explorer
        'internet_explorer.temporary_files',
        # Mozilla Firefox
        'firefox.cache',
        'firefox.session_restore',
        'firefox.vacuum',
        'winapp2_mozilla.corrupt_sqlites',
        # Opera
        'opera.cache',
        'opera.current_session']
    try:
        _out = run_program(vars_wk['BleachBit'], _args, check=False)
    except subprocess.CalledProcessError:
        print_error('  ERROR: Failed to run BleachBit.', vars_wk['LogFile'])
        if not ask('  Continue script?', vars_wk['LogFile']):
            abort()
    else:
        # Save BleachBit log
        with open('{LogDir}\\BleachBit.log'.format(**vars_wk), 'a') as f:
            f.write(_out.stdout.decode())
        # Save BleachBit (error) log
        with open('{LogDir}\\BleachBit.err.log'.format(**vars_wk), 'a') as f:
            f.write(_out.stderr.decode())

def rename_as_backup(profile_path):
    backup_path = '{path}.bak'.format(path=profile_path)
    _i = 1;
    while os.path.exists(backup_path):
        backup_path = '{path}.bak{i}'.format(i=_i, path=profile_path)
        _i += 1
    
    # print_info('    Renaming "{path}" to "{backup}"'.format(path=profile_path, backup=backup_path), vars_wk['LogFile'])
    shutil.move(profile_path, backup_path)
    
    return backup_path

def reset_internet_explorer():
    print_standard('  Internet Explorer', vars_wk['LogFile'])
    ie_exe = get_iexplorer_exe()
    
    if ask('    Reset to safe settings?', vars_wk['LogFile']):
        clean_internet_explorer()
    
    if os.path.exists(ie_exe):
        if ask('    Install Google Search and EasyLists?', vars_wk['LogFile']):
            run_program(ie_exe, ['http://www.iegallery.com/en-us/Addons/Details/813'], check=False)
    else:
        print_error('    ERROR: iexplore.exe not found. Please verify OS health.', vars_wk['LogFile'])

def reset_google_chrome():
    print_standard('  Google Chrome', vars_wk['LogFile'])
    chrome_exe = get_chrome_exe()
    profiles = get_chrome_profiles()
    
    if len(profiles) == 0:
        print_warning('    WARNING: No profiles found.', vars_wk['LogFile'])
    elif ask('    Reset profile(s) to safe settings?', vars_wk['LogFile']):
        print_info('    Closing any open windows', vars_wk['LogFile'])
        kill_process('chrome.exe')
        for profile in profiles:
            clean_chromium_profile(profile)
    
    if chrome_exe is not None:
        # Set Chrome as default browser
        run_program(chrome_exe, ['--make-default-browser'], check=False)
        
        # Install uBlock Origin?
        if ask('    Install uBlock Origin?', vars_wk['LogFile']):
            run_program(chrome_exe, ['https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en'], check=False)
    
    # Google Chrome Canary
    chrome_canary_exe = get_chrome_canary_exe()
    profiles = get_chrome_canary_profiles()
    
    if len(profiles) > 0:
        print_standard('  Google Chrome Canary', vars_wk['LogFile'])
        if ask('    Reset profile(s) to safe settings?', vars_wk['LogFile']):
            print_info('    Closing any open windows', vars_wk['LogFile'])
            kill_process('chrome.exe')
            for profile in profiles:
                clean_chromium_profile(profile)
    
        if chrome_canary_exe is not None:
            # Install uBlock Origin?
            if ask('    Install uBlock Origin?', vars_wk['LogFile']):
                run_program(chrome_canary_exe, ['https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en'], check=False)

def reset_mozilla_firefox():
    print_standard('  Mozilla Firefox', vars_wk['LogFile'])
    firefox_exe = get_firefox_exe()
    firefox_dev_exe = get_firefox_dev_exe()
    profiles = get_firefox_profiles()
    
    if firefox_exe is None and firefox_dev_exe is None:
        print_error('    ERROR: firefox.exe not found. Please verify installation.', vars_wk['LogFile'])
    
    if len(profiles) == 0:
        print_warning('    WARNING: No profiles found.', vars_wk['LogFile'])
        create_firefox_default_profiles()
    elif ask('    Reset profile(s) to safe settings?', vars_wk['LogFile']):
        print_info('    Closing any open windows', vars_wk['LogFile'])
        kill_process('firefox.exe')
        for profile in profiles:
            clean_firefox_profile(profile)
    
    if ask('    Install uBlock Origin?', vars_wk['LogFile']):
        # Install uBlock Origin
        if firefox_exe is not None:
            run_program(firefox_exe, ['https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'], check=False)
        if firefox_dev_exe is not None:
            run_program(firefox_dev_exe, ['https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'], check=False)

def reset_opera():
    print_standard('  Opera', vars_wk['LogFile'])
    opera_exe = get_opera_exe()
    profiles = get_opera_profile()
    
    # Bail early
    if opera_exe is None and len(profiles) == 0:
        print_warning('    Opera not installed and no profiles found.')
        return
    
    if opera_exe is None:
        print_error('    ERROR: Opera not installed.', vars_wk['LogFile'])
    
    if len(profiles) == 0:
        print_warning('    WARNING: No profiles found.', vars_wk['LogFile'])
    else:
        # Reset browser
        if ask('    Reset profile to safe settings?', vars_wk['LogFile']):
            print_info('    Closing any open windows', vars_wk['LogFile'])
            kill_process('opera.exe')
            clean_chromium_profile(profiles[0])

    if opera_exe is not None:
        # Install uBlock Origin?
        if ask('    Install uBlock Origin?', vars_wk['LogFile']):
            run_program(opera_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)

def reset_opera_beta():
    opera_beta_exe = get_opera_beta_exe()
    profiles = get_opera_beta_profile()
    
    # Bail early
    if opera_beta_exe is None and len(profiles) == 0:
        print_error('  Opera Beta not installed and no profiles found.')
        return
    else:
        print_standard('  Opera Beta', vars_wk['LogFile'])
    
    if opera_beta_exe is None:
        print_error('    ERROR: Opera Beta not installed.', vars_wk['LogFile'])
    
    if len(profiles) == 0:
        print_warning('    WARNING: No profiles found.', vars_wk['LogFile'])
    else:
        # Reset browser
        if ask('    Reset profile to safe settings?', vars_wk['LogFile']):
            print_info('    Closing any open windows', vars_wk['LogFile'])
            kill_process('opera.exe')
            clean_chromium_profile(profiles[0])

    if opera_beta_exe is not None:
        # Install uBlock Origin?
        if ask('    Install uBlock Origin?', vars_wk['LogFile']):
            run_program(opera_beta_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)

def reset_opera_dev():
    opera_dev_exe = get_opera_dev_exe()
    profiles = get_opera_dev_profile()
    
    # Bail early
    if opera_dev_exe is None and len(profiles) == 0:
        print_error('  Opera Dev not installed and no profiles found.')
        return
    else:
        print_standard('  Opera Dev', vars_wk['LogFile'])
    
    if opera_dev_exe is None:
        print_error('    ERROR: Opera Dev not installed.', vars_wk['LogFile'])
    
    if len(profiles) == 0:
        print_warning('    WARNING: No profiles found.', vars_wk['LogFile'])
    else:
        # Reset browser
        if ask('    Reset profile to safe settings?', vars_wk['LogFile']):
            print_info('    Closing any open windows', vars_wk['LogFile'])
            kill_process('opera.exe')
            clean_chromium_profile(profiles[0])

    if opera_dev_exe is not None:
        # Install uBlock Origin?
        if ask('    Install uBlock Origin?', vars_wk['LogFile']):
            run_program(opera_dev_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)
    
if __name__ == '__main__':
    stay_awake(vars_wk)
    
    # Reset prep
    backup_browsers()
    remove_temp_files()
    
    # Reset Browsers
    print_info('* Resetting browsers', vars_wk['LogFile'])
    reset_internet_explorer()
    reset_google_chrome()
    reset_mozilla_firefox()
    reset_opera()
    reset_opera_beta()
    reset_opera_dev()
    
    # Done
    print_standard('Done.', vars_wk['LogFile'])
    extract_item('Notepad2', vars_wk, silent=True)
    subprocess.Popen([vars_wk['Notepad2'], vars_wk['LogFile']])
    
    # Quit
    kill_process('caffeine.exe')
    exit_script()