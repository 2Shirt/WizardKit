# Wizard Kit: Functions - SafeMode

from functions.common import *


# STATIC VARIABLES
REG_MSISERVER = r'HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer'


def disable_safemode_msi():
  """Disable MSI access under safemode."""
  cmd = ['reg', 'delete', REG_MSISERVER, '/f']
  run_program(cmd)


def disable_safemode():
  """Edit BCD to remove safeboot value."""
  cmd = ['bcdedit', '/deletevalue', '{default}', 'safeboot']
  run_program(cmd)


def enable_safemode_msi():
  """Enable MSI access under safemode."""
  cmd = ['reg', 'add', REG_MSISERVER, '/f']
  run_program(cmd)
  cmd = ['reg', 'add', REG_MSISERVER, '/ve',
      '/t', 'REG_SZ', '/d', 'Service', '/f']
  run_program(cmd)


def enable_safemode():
  """Edit BCD to set safeboot as default."""
  cmd = ['bcdedit', '/set', '{default}', 'safeboot', 'network']
  run_program(cmd)


def reboot(delay=3):
  cmd = ['shutdown', '-r', '-t', '{}'.format(delay)]
  run_program(cmd, check=False)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
