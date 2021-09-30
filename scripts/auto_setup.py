"""Wizard Kit: Auto System Setup Tool"""
# vim: sts=2 sw=2 ts=2

import os
import sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk # pylint: disable=wrong-import-position


# STATIC VARIABLES
PRESETS = {
  'Default': {}, # Will be built at runtime using BASE_MENUS
  'Additional User': {
    'Configure System': (
      'Chrome Notifications',
      'Open Shell',
      'uBlock Origin',
      'Enable BSoD MiniDumps',
      'Enable RegBack',
      'Enable System Restore',
      'Set System Restore Size',
      'Enable Windows Updates',
      'Windows Explorer',
      ),
    'Install Software': (
      'Firefox', # Needed to handle profile upgrade nonsense
      ),
    'System Summary': (
      'Operating System',
      'Windows Activation',
      'Secure Boot',
      'Installed RAM',
      'Storage Status',
      'Virus Protection',
      'Partitions 4K Aligned',
      ),
    },
  'Hardware': {
    'Configure System': (
      'Enable BSoD MiniDumps',
      'Enable RegBack',
      'Enable System Restore',
      'Set System Restore Size',
      'Enable Windows Updates',
      ),
    'System Information': (
      'Backup Registry',
      ),
    'System Summary': (
      'Operating System',
      'Windows Activation',
      'Secure Boot',
      'Installed RAM',
      'Storage Status',
      'Virus Protection',
      'Partitions 4K Aligned',
      ),
    'Run Programs': (
      'Device Manager',
      'HWiNFO Sensors',
      'XMPlay',
      ),
    },
  'Verify': {
    'Configure System': (
      'Enable BSoD MiniDumps',
      'Enable RegBack',
      'Enable System Restore',
      'Set System Restore Size',
      'Enable Windows Updates',
      'Windows Explorer',
      ),
    'System Summary': (
      'Operating System',
      'Windows Activation',
      'Secure Boot',
      'Installed RAM',
      'Storage Status',
      'Virus Protection',
      'Installed Office',
      'Partitions 4K Aligned',
      ),
    },
  }

# Classes
class MenuEntry():
  # pylint: disable=too-few-public-methods
  """Simple class to allow cleaner code below."""
  def __init__(self, name, function=None, selected=True, **kwargs):
    self.name = name
    self.details = {
      'Function': function,
      'Selected': selected,
      **kwargs,
      }


# STATIC VARIABLES
BASE_MENUS = {
  'Groups': {
    'Backup Settings': (
      MenuEntry('Backup Browsers',          'auto_backup_browser_profiles'),
      MenuEntry('Backup Power Plans',       'auto_backup_power_plans'),
      MenuEntry('Reset Power Plans',        'auto_reset_power_plans'),
      MenuEntry('Set Custom Power Plan',    'auto_set_custom_power_plan'),
      ),
    'Install Software': (
      MenuEntry('Visual C++ Runtimes',      'auto_install_vcredists'),
      MenuEntry('Firefox',                  'auto_install_firefox'),
      MenuEntry('LibreOffice',              'auto_install_libreoffice', selected=False),
      MenuEntry('Open Shell',               'auto_install_open_shell'),
      MenuEntry('Software Bundle',          'auto_install_software_bundle'),
      ),
    'Configure System': (
      MenuEntry('Configure Browsers',       'auto_config_browsers'),
      MenuEntry('Open Shell',               'auto_config_open_shell'),
      MenuEntry('Enable BSoD MiniDumps',    'auto_enable_bsod_minidumps'),
      MenuEntry('Enable RegBack',           'auto_enable_regback'),
      MenuEntry('Enable System Restore',    'auto_system_restore_enable'),
      MenuEntry('Set System Restore Size',  'auto_system_restore_set_size'),
      MenuEntry('Enable Windows Updates',   'auto_windows_updates_enable'),
      MenuEntry('User Account Control',     'auto_restore_default_uac'),
      MenuEntry('Windows Activation',       'auto_activate_windows'),
      MenuEntry('Windows Explorer',         'auto_config_explorer'),
      MenuEntry(r'Windows\Temp Fix',        'auto_windows_temp_fix'),
      MenuEntry('Create System Restore',    'auto_system_restore_create'),
      ),
    'System Information': (
      MenuEntry('AIDA64 Report',            'auto_export_aida64_report'),
      MenuEntry('Backup Registry',          'auto_backup_registry'),
      ),
    'System Summary': (
      MenuEntry('Operating System',         'auto_show_os_name'),
      MenuEntry('Windows Activation',       'auto_show_os_activation'),
      MenuEntry('Secure Boot',              'auto_show_secure_boot_status'),
      MenuEntry('Installed RAM',            'auto_show_installed_ram'),
      MenuEntry('Storage Status',           'auto_show_storage_status'),
      MenuEntry('Virus Protection',         'auto_show_installed_antivirus'),
      MenuEntry('Partitions 4K Aligned',    'auto_show_4k_alignment_check'),
      ),
    'Run Programs': (
      MenuEntry('Device Manager',           'auto_open_device_manager'),
      MenuEntry('HWiNFO Sensors',           'auto_open_hwinfo_sensors'),
      MenuEntry('Windows Activation',       'auto_open_windows_activation'),
      MenuEntry('Windows Updates',          'auto_open_windows_updates'),
      MenuEntry('XMPlay',                   'auto_open_xmplay'),
      ),
    },
  'Actions': (
    MenuEntry('Load Preset'),
    MenuEntry('Start', Separator=True),
    MenuEntry('Quit'),
    ),
  }


if __name__ == '__main__':
  try:
    wk.setup.win.run_auto_setup(BASE_MENUS, PRESETS)
  except KeyboardInterrupt:
    wk.std.abort()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
