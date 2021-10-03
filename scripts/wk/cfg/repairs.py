"""WizardKit: Config - Repairs"""
# vim: sts=2 sw=2 ts=2

from wk.cfg.main import KIT_NAME_FULL

AUTO_REPAIR_DELAY_IN_SECONDS = 30
AUTO_REPAIR_KEY = fr'Software\{KIT_NAME_FULL}\Auto Repairs'
BLEACH_BIT_CLEANERS = (
  # Applications
  'adobe_reader.cache',
  'adobe_reader.tmp',
  'flash.cache',
  'gimp.tmp',
  'hippo_opensim_viewer.cache',
  'java.cache',
  'miro.cache',
  'openofficeorg.cache',
  'pidgin.cache',
  'secondlife_viewer.Cache',
  'thunderbird.cache',
  'vuze.cache',
  'yahoo_messenger.cache',
  # Browsers
  'chromium.cache',
  'chromium.session',
  'firefox.cache',
  'firefox.session_restore',
  'google_chrome.cache',
  'google_chrome.session',
  'google_earth.temporary_files',
  'opera.cache',
  'opera.session',
  'safari.cache',
  'seamonkey.cache',
  # System
  'system.clipboard',
  'system.tmp',
  'winapp2_windows.jump_lists',
  'winapp2_windows.ms_search',
  'windows_explorer.run',
  'windows_explorer.search_history',
  'windows_explorer.thumbnails',
  )
POWER_PLANS = {
  'Balanced':         '381b4222-f694-41f0-9685-ff5bb260df2e',
  'Custom':           '01189998-8199-9119-725c-ccccccccccc3',
  'High Performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
  }
REG_UAC_DEFAULT_SETTINGS = {
  'HKLM': {
    r'Software\Microsoft\Windows\CurrentVersion\Policies\System': (
      ('ConsentPromptBehaviorAdmin', 5, 'DWORD'),
      ('ConsentPromptBehaviorUser', 3, 'DWORD'),
      ('EnableLUA', 1, 'DWORD'),
      ('PromptOnSecureDesktop', 1, 'DWORD'),
      ),
    },
  }
WIDTH = 50



if __name__ == '__main__':
  print("This file is not meant to be called directly.")
