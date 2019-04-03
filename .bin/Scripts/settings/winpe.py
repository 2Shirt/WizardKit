# Wizard Kit: Settings - WinPE

from settings.data import *

# FastCopy
FAST_COPY_PE_ARGS = [
  '/cmd=noexist_only',
  '/utf8',
  '/skip_empty_dir',
  '/linkdest',
  '/no_ui',
  '/auto_close',
  '/exclude={}'.format(';'.join(FAST_COPY_EXCLUDES)),
  ]

# General
PE_TOOLS = {
  'BlueScreenView': {
    'Path': r'BlueScreenView\BlueScreenView.exe',
    },
  'FastCopy': {
    'Path': r'FastCopy\FastCopy.exe',
    'Args': FAST_COPY_PE_ARGS,
    },
  'HWiNFO': {
    'Path': r'HWiNFO\HWiNFO.exe',
    },
  'NT Password Editor': {
    'Path': r'NT Password Editor\ntpwedit.exe',
    },
  'Notepad++': {
    'Path': r'NotepadPlusPlus\NotepadPlusPlus.exe',
    },
  'PhotoRec': {
    'Path': r'TestDisk\photorec_win.exe',
    'Args': ['-new_console:n'],
    },
  'Prime95': {
    'Path': r'Prime95\prime95.exe',
    },
  'ProduKey': {
    'Path': r'ProduKey\ProduKey.exe',
    },
  'Q-Dir': {
    'Path': r'Q-Dir\Q-Dir.exe',
    },
  'TestDisk': {
    'Path': r'TestDisk\testdisk_win.exe',
    'Args': ['-new_console:n'],
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
