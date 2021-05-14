"""WizardKit: Config - UFD"""
# vim: sts=2 sw=2 ts=2

from collections import OrderedDict

from wk.cfg.main import KIT_NAME_FULL


# General
SOURCES = OrderedDict({
  'Linux':            {'Arg': '--linux',          'Type': 'ISO'},
  'Linux (Minimal)':  {'Arg': '--linux-minimal',  'Type': 'ISO'},
  'WinPE':            {'Arg': '--winpe',          'Type': 'ISO'},
  'Main Kit':         {'Arg': '--main-kit',       'Type': 'KIT'},
  'Extra Dir':        {'Arg': '--extra-dir',      'Type': 'DIR'},
  })

# Definitions: Boot entries
BOOT_ENTRIES = {
  # Path to check:      Comment to remove
  '/arch_minimal':      'UFD-MINIMAL',
  '/sources/boot.wim':  'UFD-WINPE',
  }
BOOT_FILES = {
  # Directory:  extension
  '/syslinux':  'cfg',
  '/EFI/boot':  'conf',
  }

# Definitions: Sources and Destinations
## NOTES: Paths are relative to the root of the ISO/UFD
##        Sources use rsync's trailing slash syntax
ITEMS = {
  'Extra Dir': (
    ('/',                                     '/'),
    ),
  'Linux': (
    ('/arch',                                 '/'),
    ('/EFI/boot',                             '/EFI/'),
    ('/syslinux',                             '/'),
    ),
  'Linux (Minimal)': (
    ('/arch/boot/x86_64/initramfs-linux.img', '/arch_minimal/'),
    ('/arch/boot/x86_64/vmlinuz-linux',       '/arch_minimal/'),
    ('/arch/pkglist.x86_64.txt',              '/arch_minimal/'),
    ('/arch/x86_64',                          '/arch_minimal/'),
    ),
  'Main Kit': (
    ('/',                                     f'/{KIT_NAME_FULL}/'),
    ),
  'WinPE': (
    ('/bootmgr',                              '/'),
    ('/bootmgr.efi',                          '/'),
    ('/en_us',                                '/'),
    ('/Boot/',                                '/boot/'),
    ('/EFI/Boot/',                            '/EFI/Microsoft/'),
    ('/EFI/Microsoft/',                       '/EFI/Microsoft/'),
    ('/Boot/BCD',                             '/sources/'),
    ('/Boot/boot.sdi',                        '/sources/'),
    ('/bootmgr',                              '/sources/'),
    ('/sources/boot.wim',                     '/sources/'),
    ),
  }
ITEMS_HIDDEN = (
  # Linux (all versions)
  'arch',
  'arch_minimal',
  'EFI',
  'syslinux',
  # Main Kit
  f'{KIT_NAME_FULL}/.bin',
  f'{KIT_NAME_FULL}/.cbin',
  # WinPE
  'boot',
  'bootmgr',
  'bootmgr.efi',
  'en-us',
  'images',
  'sources',
  )


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
