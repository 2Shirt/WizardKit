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
  def __init__(self, name, function=None, **kwargs):
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
      'Selected': False,
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
      MenuEntry('Enable RegBack',           'auto_enable_regback'),
      MenuEntry('Enable System Restore',    'auto_system_restore_enable'),
      MenuEntry('Set System Restore Size',  'auto_system_restore_set_size'),
      MenuEntry('Create System Restore',    'auto_system_restore_create'),
      #MenuEntry('Backup Browsers',          #TODO),
      MenuEntry('Backup Power Plans',       'auto_backup_power_plans'),
      MenuEntry('Backup Registry',          'auto_backup_registry'),
      ),
    'Windows Repairs': (
      MenuEntry('Disable Windows Updates',  'auto_windows_updates_disable'),
      MenuEntry('Reset Windows Updates',    'auto_windows_updates_reset'),
      MenuEntry('Reboot',                   'auto_reboot'),
      MenuEntry('CHKDSK',                   'auto_chkdsk'),
      MenuEntry('DISM RestoreHealth',       'auto_dism'),
      MenuEntry('SFC Scan',                 'auto_sfc'),
      MenuEntry('Clear Proxy Settings',     'auto_reset_proxy'),
      MenuEntry('Disable Pending Renames',  'auto_disable_pending_renames'),
      MenuEntry('Registry Repairs',         'auto_repair_registry'),
      MenuEntry('Reset UAC',                'auto_restore_uac_defaults'),
      MenuEntry('Reset Windows Policies',   'auto_reset_windows_policies'),
      ),
    'Malware Cleanup': (
      MenuEntry('BleachBit',                'auto_bleachbit'),
      MenuEntry('HitmanPro',                'auto_hitmanpro'),
      MenuEntry('KVRT',                     placeholder_function),
      MenuEntry('Windows Defender',         placeholder_function),
      MenuEntry('Reboot',                   'auto_reboot'),
      ),
    'Manual Steps': (
      MenuEntry('AdwCleaner',               placeholder_function),
      MenuEntry('IO Bit Uninstaller',       placeholder_function),
      MenuEntry('Enable Windows Updates',   'auto_windows_updates_enable'),
      ),
    },
  'Options': (
    MenuEntry('Kill Explorer'),
    MenuEntry('Run RKill'),
    MenuEntry('Run TDSSKiller (once)'),
    MenuEntry('Use Autologon'),
    ),
  'Actions': (
    MenuEntry('Options'),
    MenuEntry('Start', Separator=True),
    MenuEntry('Quit'),
    ),
  }


if __name__ == '__main__':
  try:
    wk.repairs.win.run_auto_repairs(BASE_MENUS)
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
