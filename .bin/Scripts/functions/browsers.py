# Wizard Kit: Functions - Browsers

from functions.common import *

# Define other_results for later try_and_print
browser_data = {}
other_results = {
    'Error': {
        'MultipleInstallationsError': 'Multiple installations detected',
        },
    'Warning': {
        'NotInstalledError': 'Not installed',
        'NoProfilesError': 'No profiles found',
        }
    }

# Regex
REGEX_BACKUP = re.compile(
    r'\.\w*bak.*',
    re.IGNORECASE)
REGEX_CHROMIUM_PROFILE = re.compile(
    r'^(Default|Profile)',
    re.IGNORECASE)
REGEX_CHROMIUM_ITEMS = re.compile(
    r'^(Bookmarks|Cookies|Favicons|Google Profile'
    r'|History|Login Data|Top Sites|TransportSecurity'
    r'|Visited Links|Web Data)',
    re.IGNORECASE)
REGEX_MOZILLA = re.compile(
    r'^(bookmarkbackups|(cookies|formhistory|places).sqlite'
    r'|key3.db|logins.json|persdict.dat)$',
    re.IGNORECASE)

# STATIC VARIABLES
DEFAULT_HOMEPAGE =      'https://www.google.com/'
IE_GALLERY =            'https://www.microsoft.com/en-us/iegallery'
MOZILLA_PREFS = {
    'browser.search.defaultenginename': '"Google"',
    'browser.search.defaultenginename.US': '"Google"',
    'browser.search.geoSpecificDefaults': 'false',
    'browser.startup.homepage': '"{}"'.format(DEFAULT_HOMEPAGE),
    'extensions.ui.lastCategory': '"addons://list/extension"',
    }
UBO_CHROME =            'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en'
UBO_CHROME_REG =        r'Software\Wow6432Node\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm'
UBO_EXTRA_CHROME =      'https://chrome.google.com/webstore/detail/ublock-origin-extra/pgdnlhfefecpicbbihgmbmffkjpaplco?hl=en'
UBO_EXTRA_CHROME_REG =  r'Software\Wow6432Node\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco'
UBO_MOZILLA =           'https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'
UBO_OPERA =             'https://addons.opera.com/en/extensions/details/ublock/?display=en'
SUPPORTED_BROWSERS = {
    'Internet Explorer': {
        'base':             'ie',
        'exe_name':         'iexplore.exe',
        'rel_install_path': 'Internet Explorer',
        'user_data_path':   r'{USERPROFILE}\Favorites',
        },
    'Google Chrome': {
        'base':             'chromium',
        'exe_name':         'chrome.exe',
        'rel_install_path': r'Google\Chrome\Application',
        'user_data_path':   r'{LOCALAPPDATA}\Google\Chrome\User Data',
        },
    'Google Chrome Canary': {
        'base':             'chromium',
        'exe_name':         'chrome.exe',
        'rel_install_path': r'Google\Chrome SxS\Application',
        'user_data_path':   r'{LOCALAPPDATA}\Google\Chrome SxS\User Data',
        },
    'Mozilla Firefox': {
        'base':             'mozilla',
        'exe_name':         'firefox.exe',
        'rel_install_path': 'Mozilla Firefox',
        'user_data_path':   r'{APPDATA}\Mozilla\Firefox\Profiles',
        },
    'Mozilla Firefox Dev': {
        'base':             'mozilla',
        'exe_name':         'firefox.exe',
        'rel_install_path': 'Firefox Developer Edition',
        'user_data_path':   r'{APPDATA}\Mozilla\Firefox\Profiles',
        },
    'Opera': {
        'base':             'chromium',
        'exe_name':         'launcher.exe',
        'rel_install_path': 'Opera',
        'user_data_path':   r'{APPDATA}\Opera Software\Opera Stable',
        },
    'Opera Beta': {
        'base':             'chromium',
        'exe_name':         'launcher.exe',
        'rel_install_path': 'Opera beta',
        'user_data_path':   r'{APPDATA}\Opera Software\Opera Next',
        },
    'Opera Dev': {
        'base':             'chromium',
        'exe_name':         'launcher.exe',
        'rel_install_path': 'Opera developer',
        'user_data_path':   r'{APPDATA}\Opera Software\Opera Developer',
        },
    }

def archive_browser(name):
    """Create backup of Browser saved in the BackupDir."""
    source = '{}*'.format(browser_data[name]['user_data_path'])
    dest = r'{BackupDir}\Browsers ({USERNAME})'.format(
        **global_vars, **global_vars['Env'])
    archive = r'{}\{}.7z'.format(dest, name)
    os.makedirs(dest, exist_ok=True)
    cmd = [
        global_vars['Tools']['SevenZip'],
        'a', '-aoa', '-bso0', '-bse0', '-mx=1',
        archive, source]
    run_program(cmd)

def backup_browsers():
    """Create backup of all detected browser profiles."""
    for name in [k for k, v in sorted(browser_data.items()) if v['profiles']]:
        try_and_print(message='{}...'.format(name),
        function=archive_browser, name=name)

def clean_chromium_profile(profile):
    """Renames profile, creates a new folder, and copies the user data to it."""
    if profile is None:
        raise Exception
    backup_path = '{path}_{Date}.bak'.format(
        path=profile['path'], **global_vars)
    backup_path = non_clobber_rename(backup_path)
    shutil.move(profile['path'], backup_path)
    os.makedirs(profile['path'], exist_ok=True)

    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_CHROMIUM_ITEMS.search(entry.name):
            shutil.copy(entry.path, r'{}\{}'.format(
                profile['path'], entry.name))

def clean_internet_explorer(**kwargs):
    """Uses the built-in function to reset IE and sets the homepage.
    
    NOTE: kwargs set but unused as a workaround."""
    kill_process('iexplore.exe')
    run_program(['rundll32.exe', 'inetcpl.cpl,ResetIEtoDefaults'], check=False)
    key = r'Software\Microsoft\Internet Explorer\Main'

    # Set homepage
    with winreg.OpenKey(HKCU, key, access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'Start Page', 0,
            winreg.REG_SZ, DEFAULT_HOMEPAGE)
        try:
            winreg.DeleteValue(_key, 'Secondary Start Pages')
        except FileNotFoundError:
            pass

def clean_mozilla_profile(profile):
    """Renames profile, creates a new folder, and copies the user data to it."""
    if profile is None:
        raise Exception
    backup_path = '{path}_{Date}.bak'.format(
        path=profile['path'], **global_vars)
    backup_path = non_clobber_rename(backup_path)
    shutil.move(profile['path'], backup_path)
    homepages = []
    os.makedirs(profile['path'], exist_ok=True)

    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_MOZILLA.search(entry.name):
            if entry.is_dir():
                shutil.copytree(entry.path, r'{}\{}'.format(
                    profile['path'], entry.name))
            else:
                shutil.copy(entry.path, r'{}\{}'.format(
                    profile['path'], entry.name))

    # Set profile defaults
    with open(r'{path}\prefs.js'.format(**profile), 'a', encoding='ascii') as f:
        for k, v in MOZILLA_PREFS.items():
            f.write('user_pref("{}", {});\n'.format(k, v))

def get_browser_details(name):
    """Get installation status and profile details for all supported browsers."""
    browser = SUPPORTED_BROWSERS[name].copy()
    
    # Update user_data_path
    browser['user_data_path'] = browser['user_data_path'].format(
        **global_vars['Env'])
    
    # Find executable (if multiple files are found, the last one is used)
    exe_path = None
    num_installs = 0
    for install_path in ['LOCALAPPDATA', 'PROGRAMFILES(X86)', 'PROGRAMFILES']:
        test_path = r'{install_path}\{rel_install_path}\{exe_name}'.format(
            install_path = global_vars['Env'].get(install_path, ''),
            **browser)
        if os.path.exists(test_path):
            num_installs += 1
            exe_path = test_path
    
    # Find profile(s)
    profiles = []
    if browser['base'] == 'ie':
        profiles.append({'name': 'Default', 'path': None})
    elif 'Google Chrome' in name:
        profiles.extend(
            get_chromium_profiles(
                search_path=browser['user_data_path']))
    elif browser['base'] == 'mozilla':
        dev = 'Dev' in name
        profiles.extend(
            get_mozilla_profiles(
                search_path=browser['user_data_path'], dev=dev))
        if exe_path and not dev and len(profiles) == 0:
            # e.g. If Firefox is installed but no profiles were found.
            ## Rename profiles.ini and create a new default profile
            profiles_ini_path = browser['user_data_path'].replace(
                'Profiles', 'profiles.ini')
            if os.path.exists(profiles_ini_path):
                backup_path = '{path}_{Date}.bak'.format(
                    path=profiles_ini_path, **global_vars)
                backup_path = non_clobber_rename(backup_path)
                shutil.move(profiles_ini_path, backup_path)
            run_program([exe_path, '-createprofile', 'default'], check=False)
            profiles.extend(
                get_mozilla_profiles(
                    search_path=browser['user_data_path'], dev=dev))
            
    elif 'Opera' in name:
        if os.path.exists(browser['user_data_path']):
            profiles.append(
                {'name': 'Default', 'path': browser['user_data_path']})
    
    # Get homepages
    if browser['base'] == 'ie':
        # IE is set to only have one profile above
        profiles[0]['homepages'] = get_ie_homepages()
    elif browser['base'] == 'mozilla':
        for profile in profiles:
            prefs_path = r'{path}\prefs.js'.format(**profile)
            profile['homepages'] = get_mozilla_homepages(prefs_path=prefs_path)
    
    # Add to browser_data
    browser_data[name] = browser
    browser_data[name].update({
        'exe_path': exe_path,
        'profiles': profiles,
        })
    
    # Raise installation warnings (if any)
    if num_installs == 0:
        raise NotInstalledError
    elif num_installs > 1 and browser['base'] != 'ie':
        raise MultipleInstallationsError

def get_chromium_profiles(search_path):
    """Find any chromium-style profiles and return as a list of dicts."""
    profiles = []
    try:
        for entry in os.scandir(search_path):
            if entry.is_dir() and REGEX_CHROMIUM_PROFILE.search(entry.name):
                profiles.append(entry)
                REGEX_PROFILE_BACKUP = r'\.\w+bak.*'
        profiles = [p for p in profiles if not REGEX_BACKUP.search(p.name)]
        # Convert os.DirEntries to dicts
        profiles = [{'name': p.name, 'path': p.path} for p in profiles]
    except Exception:
        pass

    return profiles

def get_ie_homepages():
    """Read homepages from the registry and return as a list."""
    homepages = []
    main_page = ''
    extra_pages = []
    key = r'Software\Microsoft\Internet Explorer\Main'
    with winreg.OpenKey(HKCU, key) as _key:
       try:
           main_page = winreg.QueryValueEx(_key, 'Start Page')[0]
       except FileNotFoundError:
           pass
       try:
           extra_pages = winreg.QueryValueEx(_key, 'Secondary Start Pages')[0]
       except FileNotFoundError:
           pass
    if main_page != '':
        homepages.append(main_page)
    if len(extra_pages) > 0:
        homepages.extend(extra_pages)
    return homepages

def get_mozilla_homepages(prefs_path):
    """Read homepages from prefs.js and return as a list."""
    homepages = []
    try:
        with open(prefs_path, 'r') as f:
            search = re.search(
                r'browser\.startup\.homepage", "([^"]*)"',
                f.read(), re.IGNORECASE)
            if search:
                homepages = search.group(1).split('|')
    except Exception:
        pass
    
    return homepages

def get_mozilla_profiles(search_path, dev=False):
    """Find any mozilla-style profiles and return as a list of dicts."""
    profiles = []
    try:
        for entry in os.scandir(search_path):
            if entry.is_dir():
                if 'dev-edition' in entry.name:
                    # NOTE: Not always present which can lead
                    # to Dev profiles being marked as non-Dev
                    ## NOTE 2: It is possible that a non-Dev profile
                    ##      to be created with 'dev-edition' in the name.
                    ##      (It wouldn't make sense, but possible)
                    if dev:
                        profiles.append(entry)
                elif not dev:
                    profiles.append(entry)
        profiles = [p for p in profiles if not REGEX_BACKUP.search(p.name)]
        # Convert os.DirEntries to dicts
        profiles = [{'name': p.name, 'path': p.path} for p in profiles]
    except Exception:
        pass

    return profiles

def install_adblock(indent=8, width=32):
    """Install adblock for all supported browsers."""
    for browser in sorted(browser_data):
        exe_path = browser_data[browser].get('exe_path', None)
        function=run_program
        if not exe_path:
            if browser_data[browser]['profiles']:
                print_standard(
                    '{indent}{browser:<{width}}'.format(
                        indent=' '*indent, width=width, browser=browser+'...'),
                    end='', flush=True)
                print_warning('Profile(s) detected but browser not installed',
                    timestamp=False)
            else:
                # Only warn if profile(s) are detected.
                pass
        else:
            # Set urls to open
            urls = []
            if browser_data[browser]['base'] == 'chromium':
                if browser == 'Google Chrome':
                    # Check for system exensions
                    try:
                        winreg.QueryValue(HKLM, UBO_CHROME_REG)
                    except FileNotFoundError:
                        urls.append(UBO_CHROME)
                    try:
                        winreg.QueryValue(HKLM, UBO_EXTRA_CHROME_REG)
                    except FileNotFoundError:
                        urls.append(UBO_EXTRA_CHROME)
                    
                    if len(urls) == 0:
                        urls = ['chrome://extensions']
                elif 'Opera' in browser:
                    urls.append(UBO_OPERA)
                else:
                    urls.append(UBO_CHROME)
                    urls.append(UBO_EXTRA_CHROME)
            
            elif browser_data[browser]['base'] == 'mozilla':
                # Assume UBO is not installed first and change if it is
                urls.append(UBO_MOZILLA)
                if browser == 'Mozilla Firefox':
                    ubo = browser_data[browser]['exe_path'].replace(
                        'firefox.exe',
                        r'distribution\extensions\uBlock0@raymondhill.net')
                    if os.path.exists(ubo):
                        urls = ['about:addons']
            
            elif browser_data[browser]['base'] == 'ie':
                urls.append(IE_GALLERY)
                function=popen_program
            
            # By using check=False we're skipping any return codes so
            # it should only fail if the program can't be run
            #   (or can't be found).
            # In other words, this isn't tracking the addon/extension's
            #   installation status.
            try_and_print(message='{}...'.format(browser),
                indent=indent, width=width,
                cs='Done', function=function,
                cmd=[exe_path, *urls], check=False)

def list_homepages(indent=8, width=32):
    """List current homepages for reference."""
    
    for browser in [k for k, v in sorted(browser_data.items()) if v['exe_path']]:
        # Skip Chromium-based browsers
        if browser_data[browser]['base'] == 'chromium':
            print_info(
                '{indent}{browser:<{width}}'.format(
                    indent=' '*indent, width=width, browser=browser+'...'),
                end='', flush=True)
            print_warning('Not implemented', timestamp=False)
            continue
        
        # All other browsers
        print_info('{indent}{browser:<{width}}'.format(
            indent=' '*indent, width=width, browser=browser+'...'))
        for profile in browser_data[browser].get('profiles', []):
            name = profile.get('name', '?')
            homepages = profile.get('homepages', [])
            if len(homepages) == 0:
                print_standard(
                    '{indent}{name:<{width}}'.format(
                        indent=' '*indent, width=width, name=name),
                    end='', flush=True)
                print_warning('None found', timestamp=False)
            else:
                for page in homepages:
                    print_standard('{indent}{name:<{width}}{page}'.format(
                        indent=' '*indent, width=width, name=name, page=page))

def reset_browsers(indent=8, width=32):
    """Reset all detected browsers to safe defaults."""
    for browser in [k for k, v in sorted(browser_data.items()) if v['profiles']]:
        print_info('{indent}{name}'.format(indent=' '*indent, name=browser))
        for profile in browser_data[browser]['profiles']:
            if browser_data[browser]['base'] == 'chromium':
                function = clean_chromium_profile
            elif browser_data[browser]['base'] == 'ie':
                function = clean_internet_explorer
            elif browser_data[browser]['base'] == 'mozilla':
                function = clean_mozilla_profile
            try_and_print(
                message='{}...'.format(profile['name']),
                indent=indent, width=width, function=function,
                other_results=other_results, profile=profile)

def scan_for_browsers():
    """Scan system for any supported browsers."""
    for name in sorted(SUPPORTED_BROWSERS):
        try_and_print(message='{}...'.format(name),
            function=get_browser_details, cs='Detected',
            other_results=other_results, name=name)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
