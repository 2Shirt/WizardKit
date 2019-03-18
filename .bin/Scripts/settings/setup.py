# Wizard Kit: Settings - Setup

import os
import winreg

# General
HKU =  winreg.HKEY_USERS
HKCR = winreg.HKEY_CLASSES_ROOT
HKCU = winreg.HKEY_CURRENT_USER
HKLM = winreg.HKEY_LOCAL_MACHINE
OTHER_RESULTS = {
  'Error': {
    'CalledProcessError':   'Unknown Error',
    'FileNotFoundError':  'File not found',
    },
  'Warning': {},
  }

# Browsers
MOZILLA_FIREFOX_UBO_PATH = r'{}\{}\ublock_origin.xpi'.format(
  os.environ.get('PROGRAMFILES'),
  r'Mozilla Firefox\distribution\extensions')
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

# Classic Start
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

# Explorer
SETTINGS_EXPLORER_SYSTEM = {
  # Disable Location Tracking
  r'Software\Microsoft\Windows NT\CurrentVersion\Sensor\Overrides\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}': {
    'DWORD Items': {'SensorPermissionState': 0},
    },
  r'System\CurrentControlSet\Services\lfsvc\Service\Configuration': {
    'Status': {'Value': 0},
    },
  # Disable Telemetry
  r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection': {
    # Using SOFTWARE in all caps to avoid collision with 32-bit setting below
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
  # Disable features
  r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager': {
    'DWORD Items': {
      # Silently installed apps
      'SilentInstalledAppsEnabled': 0,
      # Tips and Tricks
      'SoftLandingEnabled ': 0,
      'SubscribedContent-338389Enabled': 0,
      },
    },
  # File Explorer
  r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced': {
    'DWORD Items': {
    # Change default Explorer view to "Computer"
      'LaunchTo': 1,
      },
    },
  # Hide People bar
  r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People': {
    'DWORD Items': {'PeopleBand': 0},
    },
  # Hide Search button / box
  r'Software\Microsoft\Windows\CurrentVersion\Search': {
    'DWORD Items': {'SearchboxTaskbarMode': 0},
    },
  }

# Visual C++ Runtimes
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

# Windows Updates
SETTINGS_WINDOWS_UPDATES = {
  r'Software\Microsoft\WindowsUpdate\UX\Settings': {
    'DWORD Items': {
      # Set to non-targeted readiness level
      'BranchReadinessLevel': 32,
      'DeferFeatureUpdatesPeriodInDays': 60,
      },
    }
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
