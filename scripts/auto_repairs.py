"""Wizard Kit: Auto-Repair Tool"""
# vim: sts=2 sw=2 ts=2

import os
import sys
import random # TODO: Deleteme
import time

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk # pylint: disable=wrong-import-position


# Classes
class MenuEntry():
  # pylint: disable=too-few-public-methods
  """Simple class to allow cleaner code below."""
  def __init__(self, name, function, **kwargs):
    self.name = name

    # Color reboot entries
    if name == 'Reboot':
      self.name = wk.std.color_string(
        ['Reboot', ' ', '(Forced)'],
        ['YELLOW', None, 'ORANGE'],
        sep='',
        )

    # Set details
    self.details = {
      'Function': function,
      'Selected': True,
      **kwargs,
      }


# TODO: Deleteme
TRY_AND_PRINT = wk.std.TryAndPrint()
TRY_AND_PRINT.width = 50
def placeholder_function(group, name):
  result = TRY_AND_PRINT.run(f'{name}...', time.sleep, random.randint(1, 3))
  wk.repairs.win.save_settings(group, name, result=result)

def placeholder_reboot(group, name):
  print('"Rebooting" shortly...')
  time.sleep(random.randint(1, 3))
  wk.repairs.win.save_settings(group, name, done=True, message='DONE')
  raise SystemExit


# STATIC VARIABLES
BASE_MENUS = {
  'Groups': {
    'Backup Settings': (
      MenuEntry('Enable RegBack', placeholder_function),
      MenuEntry('Enable System Restore', placeholder_function),
      MenuEntry('Create System Restore', placeholder_function),
      MenuEntry('Backup Browsers', placeholder_function),
      MenuEntry('Backup Power Plans', placeholder_function),
      MenuEntry('Backup Registry', placeholder_function),
      ),
    'Windows Repairs': (
      MenuEntry('Disable Windows Updates', placeholder_function),
      MenuEntry('Reset Windows Updates', placeholder_function),
      MenuEntry('Reboot', placeholder_reboot),
      MenuEntry('CHKDSK', placeholder_function),
      MenuEntry('DISM RestoreHealth', wk.repairs.win.auto_dism),
      MenuEntry('SFC Scan', placeholder_function),
      MenuEntry('Fix File Associations', placeholder_function),
      MenuEntry('Clear Proxy Settings', placeholder_function),
      MenuEntry('Disable Pending Renames', placeholder_function),
      MenuEntry('Registry Repairs', placeholder_function),
      MenuEntry('Repair Safe Mode', placeholder_function),
      MenuEntry('Reset UAC', placeholder_function),
      MenuEntry('Reset Windows Policies', placeholder_function),
      ),
    'Malware Cleanup': (
      MenuEntry('BleachBit', placeholder_function),
      MenuEntry('HitmanPro', placeholder_function),
      MenuEntry('KVRT', placeholder_function),
      MenuEntry('Windows Defender', placeholder_function),
      MenuEntry('Reboot', placeholder_reboot),
      ),
    'Manual Steps': (
      MenuEntry('AdwCleaner', placeholder_function),
      MenuEntry('IO Bit Uninstaller', placeholder_function),
      MenuEntry('Enable Windows Updates', placeholder_function),
      ),
    },
  'Options': (
    MenuEntry('Kill Explorer', placeholder_function),
    MenuEntry('Run RKill at startup', placeholder_function),
    MenuEntry('Use Autologon', placeholder_function),
    ),
  'Actions': (
    MenuEntry('Options', placeholder_function),
    MenuEntry('Start', placeholder_function, Separator=True),
    MenuEntry('Quit', placeholder_function),
    ),
  }


if __name__ == '__main__':
  try:
    wk.repairs.win.run_auto_repairs(BASE_MENUS)
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
