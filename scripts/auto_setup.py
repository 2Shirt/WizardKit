"""Wizard Kit: Auto System Setup Tool"""
# vim: sts=2 sw=2 ts=2

import os
import sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk # pylint: disable=wrong-import-position


# STATIC VARIABLES
PRESETS = {
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
      'Storage Volumes',
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
      'Storage Volumes',
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
      'Storage Volumes',
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
  def __init__(self, name, function=None, **kwargs):
    self.name = name
    self.details = {
      'Function': function,
      'Selected': True,
      **kwargs,
      }


# TODO: DELETEME
def no_op(*args):
  """No Op"""

# STATIC VARIABLES
BASE_MENUS = {
  'Groups': {
    'Backup Settings': (
      # Add checks for existing backups and skip if detected
      MenuEntry('Backup Browsers',          'auto_backup_browser_profiles'),
      MenuEntry('Backup Power Plans',       'auto_backup_power_plans'),
      MenuEntry('Reset Power Plans',        'auto_reset_power_plans'),
      MenuEntry('Set Custom Power Plan',    'auto_set_custom_power_plan'),
      ),
    'Install Software': (
      MenuEntry('Visual C++ Runtimes',      'auto_install_vcredists'),
      #MenuEntry('ESET NOD32 Antivirus',     no_op),
      MenuEntry('Firefox',                  'auto_install_firefox'),
      MenuEntry('LibreOffice',              'auto_install_libreoffice'),
      MenuEntry('Open Shell',               'auto_install_open_shell'),
      MenuEntry('Software Bundle',          'auto_install_software_bundle'),
      ),
    'Configure System': (
      MenuEntry('Chrome Notifications',     'auto_disable_chrome_notifications'),
      #MenuEntry('O&O ShutUp 10',            no_op),
      MenuEntry('Open Shell',               'auto_config_open_shell'),
      MenuEntry('uBlock Origin',            'auto_enable_ublock_origin'),
      #MenuEntry('Disable Fast Startup',     no_op),
      MenuEntry('Enable BSoD MiniDumps',    no_op),
      #MenuEntry('Enable Hibernation',       no_op),
      MenuEntry('Enable RegBack',           'auto_enable_regback'),
      MenuEntry('Enable System Restore',    'auto_system_restore_enable'),
      MenuEntry('Set System Restore Size',  'auto_system_restore_set_size'),
      MenuEntry('Create System Restore',    'auto_system_restore_create'),
      MenuEntry('Enable Windows Updates',   'auto_windows_updates_enable'),
      MenuEntry('User Account Control',     no_op),
      MenuEntry('Windows Activation',       no_op),
      MenuEntry('Windows Explorer',         no_op),
      MenuEntry(r'Windows\Temp Fix',        no_op),
      ),
    'System Information': (
      MenuEntry('AIDA64 Reports',           no_op),
      MenuEntry('Backup Registry',          'auto_backup_registry'),
      MenuEntry('Everything (File List)',   no_op),
      ),
    'System Summary': (
      MenuEntry('Operating System',         no_op),
      MenuEntry('Windows Activation',       no_op),
      MenuEntry('Secure Boot',              no_op),
      MenuEntry('Installed RAM',            no_op),
      MenuEntry('Storage Volumes',          no_op),
      MenuEntry('Virus Protection',         no_op),
      MenuEntry('Partitions 4K Aligned',    no_op),
      ),
    'Run Programs': (
      MenuEntry('Device Manager',           no_op),
      MenuEntry('HWiNFO Sensors',           no_op),
      #MenuEntry('Snappy Driver Installer',  no_op),
      MenuEntry('Windows Updates',          no_op),
      MenuEntry('Windows Activation',       no_op),
      MenuEntry('XMPlay',                   no_op),
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
