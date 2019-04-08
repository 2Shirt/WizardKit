# Wizard Kit: Settings - UFD

from settings.main import *

# General
DOCSTRING = '''WizardKit: Build UFD

Usage:
  build-ufd [options] --ufd-device PATH --linux-iso PATH
            [--linux-minimal-iso PATH]
            [--main-kit PATH]
            [--winpe-iso PATH]
            [--extra-dir PATH]
  build-ufd (-h | --help)

Options:
  -e PATH, --extra-dir PATH
  -k PATH, --main-kit PATH
  -l PATH, --linux-iso PATH
  -m PATH, --linux-minimal-iso PATH
  -u PATH, --ufd-device PATH
  -w PATH, --winpe-iso PATH

  -d --debug            Enable debug mode
  -h --help             Show this page
  -v --verbose          Enable verbose mode
  -M --use-mbr          Use real MBR instead of GPT w/ Protective MBR
  -F --force            Bypass all confirmation messages. USE WITH EXTREME CAUTION!
  -U --update           Don't format device, just update
'''
ISO_LABEL = '{}_LINUX'.format(KIT_NAME_SHORT)
UFD_LABEL = '{}_UFD'.format(KIT_NAME_SHORT)
UFD_SOURCES = (
  # NOTE: Using tuple of tuples to ensure copy order
  ('Linux', '--linux-iso'),
  ('Linux (Minimal)', '--linux-minimal-iso'),
  ('WinPE', '--winpe-iso'),
  ('Main Kit', '--main-kit'),
  ('Extras', '--extra-dir'),
  )

# Definitions: Boot entries
## NOTE: if key path exists uncomment #value# lines
BOOT_ENTRIES = {
  'arch_minimal': 'MINIMAL',
  'sources/boot.wim': 'WINPE',
  }

# Definitions: Sources and Destinations
## NOTES: Paths are relative to the root of the ISO/UFD
##        Sources use rsync's trailing slash syntax
ITEMS_LINUX_FULL = (
  ('/arch',           '/'),
  ('/isolinux',       '/'),
  ('/EFI/boot',       '/EFI/'),
  ('/EFI/memtest86',  '/EFI/'),
  )
ITEMS_LINUX_MINIMAL = (
  ('/arch/boot/archiso.img',    '/arch_minimal/'),
  ('/arch/boot/vmlinuz',        '/arch_minimal/'),
  ('/arch/pkglist.x86_64.txt',  '/arch_minimal/'),
  ('/arch/x86_64',              '/arch_minimal/'),
  )
ITEMS_WINPE = (
  ('/bootmgr',          '/'),
  ('/bootmgr.efi',      '/'),
  ('/en_us',            '/'),
  ('/Boot/',            '/boot/'),
  ('/EFI/Boot/',        '/EFI/Microsoft/'),
  ('/EFI/Microsoft/',   '/EFI/Microsoft/'),
  ('/Boot/BCD',         '/sources/'),
  ('/Boot/boot.sdi',    '/sources/'),
  ('/bootmgr',          '/sources/'),
  ('/sources/boot.wim', '/sources/'),
  )

if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
