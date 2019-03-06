# Wizard Kit: Settings - Browsers

# General
DEFAULT_HOMEPAGE =      'https://www.google.com/'
IE_GALLERY =            'https://www.microsoft.com/en-us/iegallery'
MOZILLA_PREFS = {
  'browser.search.defaultenginename': '"Google"',
  'browser.search.defaultenginename.US': '"Google"',
  'browser.search.geoSpecificDefaults': 'false',
  'browser.startup.homepage': '"{}"'.format(DEFAULT_HOMEPAGE),
  'extensions.ui.lastCategory': '"addons://list/extension"',
  }
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

# uBlock Origin
UBO_CHROME =            'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en'
UBO_CHROME_REG =        r'Software\Wow6432Node\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm'
UBO_EXTRA_CHROME =      'https://chrome.google.com/webstore/detail/ublock-origin-extra/pgdnlhfefecpicbbihgmbmffkjpaplco?hl=en'
UBO_EXTRA_CHROME_REG =  r'Software\Wow6432Node\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco'
UBO_MOZILLA =           'https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'
UBO_MOZZILA_PATH =      r'{}\Mozilla Firefox\distribution\extensions\ublock_origin.xpi'.format(os.environ.get('PROGRAMFILES'))
UBO_MOZILLA_REG =       r'Software\Mozilla\Firefox\Extensions'
UBO_MOZILLA_REG_NAME =  'uBlock0@raymondhill.net'
UBO_OPERA =             'https://addons.opera.com/en/extensions/details/ublock/?display=en'


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2 tw=0
