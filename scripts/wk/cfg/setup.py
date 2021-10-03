"""WizardKit: Config - Setup"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2


BROWSER_PATHS = {
  # Relative to PROGRAMFILES_64, PROGRAMFILES_32, LOCALAPPDATA (in that order)
  'Google Chrome': 'Google/Chrome/Application/chrome.exe',
  'Mozilla Firefox': 'Mozilla Firefox/firefox.exe',
  'Microsoft Edge': 'Microsoft/Edge/Application/msedge.exe',
  'Opera': 'Opera/launcher.exe',
  }
LIBREOFFICE_XCU_DATA = '''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.presentation.Present
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.sheet.SpreadsheetDoc
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.text.TextDocument']"
<item oor:path="/org.openoffice.Office.Common/Save/Document"><prop oor:name="WarnAlienFormat" oor:op="fuse"><value>fal
</oor:items>
'''
REG_CHROME_UBLOCK_ORIGIN = {
  'HKLM': {
    r'Software\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm': (
      ('update_url', 'https://clients2.google.com/service/update2/crx', 'SZ', '32'),
      )
    },
  }
REG_WINDOWS_EXPLORER = {
  # pylint: disable=line-too-long
  'HKLM': {
    # Disable Location Tracking
    r'Software\Microsoft\Windows NT\CurrentVersion\Sensor\Overrides\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}': (
      ('SensorPermissionState', 0, 'DWORD'),
      ),
    r'System\CurrentControlSet\Services\lfsvc\Service\Configuration': (
      ('Status', 0, 'DWORD'),
      ),
    # Disable Telemetry
    r'Software\Microsoft\Windows\CurrentVersion\Policies\DataCollection': (
      ('AllowTelemetry', 0, 'DWORD'),
      ('AllowTelemetry', 0, 'DWORD', '32'),
      ),
    r'Software\Policies\Microsoft\Windows\DataCollection': (
      ('AllowTelemetry', 0, 'DWORD'),
      ),
    # Disable Wi-Fi Sense
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowWiFiHotSpotReporting': (
      ('Value', 0, 'DWORD'),
      ),
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowAutoConnectToWiFiSenseHotspots': (
      ('Value', 0, 'DWORD'),
      ),
    },
  'HKCU': {
    # Desktop theme (<= v1809 default)
    r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize': (
      ('AppsUseLightTheme', 1, 'DWORD'),
      ('SystemUsesLightTheme', 0, 'DWORD'),
      ),
    # Disable features
    r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager': (
      ('SilentInstalledAppsEnabled', 0, 'DWORD'),
      # Tips and Tricks
      ('SoftLandingEnabled ', 0, 'DWORD'),
      ('SubscribedContent-338389Enabled', 0, 'DWORD'),
      ),
    # Disable news and interests from opening on hover
    r'Software\Microsoft\Windows\CurrentVersion\Feeds': (
      ('ShellFeedsTaskbarOpenOnHover', 0, 'DWORD'),
      ),
    # File Explorer
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced': (
      # Change default Explorer view to "Computer"
      ('LaunchTo', 1, 'DWORD'),
      ('SeparateProcess', 1, 'DWORD'),
      ),
    # Hide People bar
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People': (
      ('PeopleBand', 0, 'DWORD'),
      ),
    # Hide Search button / box
    r'Software\Microsoft\Windows\CurrentVersion\Search': (
      ('SearchboxTaskbarMode', 1, 'DWORD'),
      ),
    },
  }
REG_OPEN_SHELL_SETTINGS = {
  'HKCU': {
    r'Software\OpenShell\StartMenu': (
      ('ShowedStyle2', 1, 'DWORD'),
      ),
    r'Software\OpenShell\StartMenu\Settings': (
      ('MenuStyle', 'Win7', 'SZ'),
      ('RecentPrograms', 'Recent', 'SZ'),
      ('SkinW7', 'Fluent-Metro', 'SZ'),
      ('SkinVariationW7', '', 'SZ'),
      ('SkipMetro', 1, 'DWORD'),
      (
        'SkinOptionsW7',
        [
          # NOTE: Seems to need all options specified to work?
          'DARK_MAIN=1', 'METRO_MAIN=0', 'LIGHT_MAIN=0', 'AUTOMODE_MAIN=0',
          'DARK_SUBMENU=0', 'METRO_SUBMENU=0', 'LIGHT_SUBMENU=0', 'AUTOMODE_SUBMENU=1',
          'SUBMENU_SEPARATORS=1', 'DARK_SEARCH=0', 'METRO_SEARCH=0', 'LIGHT_SEARCH=1',
          'AUTOMODE_SEARCH=0', 'SEARCH_FRAME=1', 'SEARCH_COLOR=0', 'SMALL_SEARCH=0',
          'MODERN_SEARCH=1', 'SEARCH_ITALICS=0', 'NONE=0', 'SEPARATOR=0',
          'TWO_TONE=1', 'CLASSIC_SELECTOR=1', 'HALF_SELECTOR=0', 'CURVED_MENUSEL=1',
          'CURVED_SUBMENU=0', 'SELECTOR_REVEAL=0', 'TRANSPARENT=0', 'OPAQUE_SUBMENU=1',
          'OPAQUE_MENU=0', 'OPAQUE=0', 'STANDARD=1', 'SMALL_MAIN2=0',
          'SMALL_ICONS=0', 'COMPACT_SUBMENU=0', 'PRESERVE_MAIN2=0', 'LESS_PADDING=0',
          'EXTRA_PADDING=1', '24_PADDING=0', 'LARGE_PROGRAMS=0', 'TRANSPARENT_SHUTDOWN=0',
          'OUTLINE_SHUTDOWN=0', 'BUTTON_SHUTDOWN=1', 'EXPERIMENTAL_SHUTDOWN=0', 'LARGE_FONT=0',
          'CONNECTED_BORDER=1', 'FLOATING_BORDER=0', 'LARGE_SUBMENU=0', 'LARGE_LISTS=0',
          'THIN_MAIN2=0', 'EXPERIMENTAL_MAIN2=1', 'USER_IMAGE=1', 'USER_OUTSIDE=0',
          'SCALING_USER=1', '56=0', '64=0', 'TRANSPARENT_USER=0',
          'UWP_SCROLLBAR=1', 'MODERN_SCROLLBAR=0', 'OLD_ICONS=0', 'NEW_ICONS=1',
          'SMALL_ARROWS=0', 'ICON_FRAME=0', 'SEARCH_SEPARATOR=0', 'NO_PROGRAMS_BUTTON=0',
          ],
        'MULTI_SZ',
        ),
      ),
    },
  }
UBLOCK_ORIGIN_URLS = {
  'Google Chrome':    'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm',
  'Microsoft Edge':   'https://microsoftedge.microsoft.com/addons/detail/ublock-origin/odfafepnkmbhccpbejgmiehpchacaeak',
  'Mozilla Firefox':  'https://addons.mozilla.org/addon/ublock-origin/',
  'Opera':            'https://addons.opera.com/extensions/details/ublock/',
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
