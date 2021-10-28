"""WizardKit: Config - Repairs"""
# vim: sts=2 sw=2 ts=2

from wk.cfg.main import KIT_NAME_FULL

AUTO_REPAIR_DELAY_IN_SECONDS = 30
AUTO_REPAIR_KEY = fr'Software\{KIT_NAME_FULL}\Auto Repairs'
BLEACH_BIT_CLEANERS = (
  # Applications
  'adobe_reader.cache',
  'adobe_reader.tmp',
  'amule.temp',
  'discord.cache',
  'flash.cache',
  'gimp.tmp',
  'google_earth.temporary_files',
  'gpodder.cache',
  'hippo_opensim_viewer.cache',
  'java.cache',
  'miro.cache',
  'openofficeorg.cache',
  'pidgin.cache',
  'seamonkey.cache',
  'secondlife_viewer.Cache',
  'silverlight.temp',
  'slack.cache',
  'smartftp.cache',
  'thunderbird.cache',
  'vuze.cache',
  'vuze.temp',
  'windows_media_player.cache',
  'winrar.temp',
  'yahoo_messenger.cache',
  'zoom.cache',
  # Browsers
  'brave.cache',
  'brave.session',
  'chromium.cache',
  'chromium.search_engines',
  'chromium.session',
  'firefox.cache',
  'firefox.session_restore',
  'google_chrome.cache',
  'google_chrome.session',
  'internet_explorer.cache',
  'microsoft_edge.cache',
  'microsoft_edge.session',
  'opera.cache',
  'opera.session',
  'palemoon.cache',
  'palemoon.session_restore',
  'safari.cache',
  'waterfox.cache',
  'waterfox.session_restore',
  # System
  'system.clipboard',
  'system.tmp',
  'windows_defender.temp',
  'windows_explorer.run',
  'windows_explorer.thumbnails',
  )
CUSTOM_POWER_PLAN_NAME = f'{KIT_NAME_FULL} Power Plan'
CUSTOM_POWER_PLAN_DESC = 'Customized for the best experience.'
POWER_PLANS = {
  'Balanced':         '381b4222-f694-41f0-9685-ff5bb260df2e',
  'Custom':           '01189998-8199-9119-725c-ccccccccccc3',
  'High Performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
  }
POWER_PLAN_SLEEP_TIMEOUTS = {
  'Balanced': ('1800', '900'),
  'High Performance': ('0', '0'),
  }
REG_UAC_DEFAULTS_WIN7 = {
  'HKLM': {
    r'Software\Microsoft\Windows\CurrentVersion\Policies\System': (
      ('ConsentPromptBehaviorAdmin', 5, 'DWORD'),
      ('EnableLUA', 1, 'DWORD'),
      ('PromptOnSecureDesktop', 1, 'DWORD'),
      ),
    },
  }
REG_UAC_DEFAULTS_WIN10 = {
  'HKLM': {
    r'Software\Microsoft\Windows\CurrentVersion\Policies\System': (
      ('ConsentPromptBehaviorAdmin', 5, 'DWORD'),
      ('ConsentPromptBehaviorUser', 3, 'DWORD'),
      ('EnableInstallerDetection', 1, 'DWORD'),
      ('EnableLUA', 1, 'DWORD'),
      ('EnableVirtualization', 1, 'DWORD'),
      ('PromptOnSecureDesktop', 1, 'DWORD'),
      ),
    },
  }
WIDTH = 50



if __name__ == '__main__':
  print("This file is not meant to be called directly.")
