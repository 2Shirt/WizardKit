"""WizardKit: Auto Repair Tool"""
# vim: sts=2 sw=2 ts=2

import os
import sys

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
      'Selected': True,
      **kwargs,
      }


# STATIC VARIABLES
BASE_MENUS = {
  'Groups': {
    'Backup Settings': (
      MenuEntry('Enable RegBack',           'auto_enable_regback'),
      MenuEntry('Enable System Restore',    'auto_system_restore_enable'),
      MenuEntry('Set System Restore Size',  'auto_system_restore_set_size'),
      MenuEntry('Create System Restore',    'auto_system_restore_create'),
      MenuEntry('Backup Browsers',          'auto_backup_browser_profiles'),
      MenuEntry('Backup Power Plans',       'auto_backup_power_plans'),
      MenuEntry('Reset Power Plans',        'auto_reset_power_plans'),
      MenuEntry('Set Custom Power Plan',    'auto_set_custom_power_plan'),
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
      MenuEntry('KVRT',                     'auto_kvrt'),
      MenuEntry('Windows Defender',         'auto_microsoft_defender'),
      MenuEntry('Remove Custom Power Plan', 'auto_remove_power_plan'),
      MenuEntry('Reboot',                   'auto_reboot'),
      ),
    'Manual Steps': (
      MenuEntry('AdwCleaner',               'auto_adwcleaner'),
      MenuEntry('IO Bit Uninstaller',       'auto_iobit_uninstaller'),
      MenuEntry('Enable Windows Updates',   'auto_windows_updates_enable'),
      ),
    },
  'Options': (
    MenuEntry('Kill Explorer'),
    MenuEntry('Run RKill'),
    MenuEntry('Run TDSSKiller (once)'),
    MenuEntry('Sync Clock'),
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
  except KeyboardInterrupt:
    wk.std.abort()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
