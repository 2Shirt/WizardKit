# Wizard Kit: Download the latest versions of the programs in the kit

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.update import *
init_global_vars()
os.system('title {}: Kit Update Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
  try:
    clear_screen()
    print_info('{}: Kit Update Tool\n'.format(KIT_NAME_FULL))
    other_results = {
      'Error': {
        'CalledProcessError': 'Unknown Error',
      }}

    ## Prep ##
    update_sdio = ask('Update SDI Origin?')

    ## Download ##
    print_success('Downloading tools')

    # Data Recovery
    print_info('  Data Recovery')
    try_and_print(message='TestDisk / PhotoRec...', function=update_testdisk, other_results=other_results, width=40)

    # Data Transfers
    print_info('  Data Transfers')
    try_and_print(message='FastCopy...', function=update_fastcopy, other_results=other_results, width=40)
    try_and_print(message='wimlib...', function=update_wimlib, other_results=other_results, width=40)
    try_and_print(message='XYplorer...', function=update_xyplorer, other_results=other_results, width=40)

    # Diagnostics
    print_info('  Diagnostics')
    try_and_print(message='AIDA64...', function=update_aida64, other_results=other_results, width=40)
    try_and_print(message='Autoruns...', function=update_autoruns, other_results=other_results, width=40)
    try_and_print(message='BleachBit...', function=update_bleachbit, other_results=other_results, width=40)
    try_and_print(message='Blue Screen View...', function=update_bluescreenview, other_results=other_results, width=40)
    try_and_print(message='ERUNT...', function=update_erunt, other_results=other_results, width=40)
    try_and_print(message='Hitman Pro...', function=update_hitmanpro, other_results=other_results, width=40)
    try_and_print(message='HWiNFO...', function=update_hwinfo, other_results=other_results, width=40)
    try_and_print(message='NirCmd...', function=update_nircmd, other_results=other_results, width=40)
    try_and_print(message='ProduKey...', function=update_produkey, other_results=other_results, width=40)

    # Drivers
    print_info('  Drivers')
    try_and_print(message='Intel RST...', function=update_intel_rst, other_results=other_results, width=40)
    try_and_print(message='Intel SSD Toolbox...', function=update_intel_ssd_toolbox, other_results=other_results, width=40)
    try_and_print(message='Samsing Magician...', function=update_samsung_magician, other_results=other_results, width=40)
    if update_sdio:
      try_and_print(message='Snappy Driver Installer Origin...', function=update_sdi_origin, other_results=other_results, width=40)

    # Installers
    print_info('  Installers')
    try_and_print(message='Adobe Reader DC...', function=update_adobe_reader_dc, other_results=other_results, width=40)
    try_and_print(message='Macs Fan Control...', function=update_macs_fan_control, other_results=other_results, width=40)
    try_and_print(message='MS Office...', function=update_office, other_results=other_results, width=40)
    try_and_print(message='Visual C++ Runtimes...', function=update_vcredists, other_results=other_results, width=40)
    update_all_ninite(other_results=other_results, width=40)

    # Misc
    print_info('  Misc')
    try_and_print(message='Caffeine...', function=update_caffeine, other_results=other_results, width=40)
    try_and_print(message='Classic Start Skin...', function=update_classic_start_skin, other_results=other_results, width=40)
    try_and_print(message='Du...', function=update_du, other_results=other_results, width=40)
    try_and_print(message='Everything...', function=update_everything, other_results=other_results, width=40)
    try_and_print(message='Firefox Extensions...', function=update_firefox_ublock_origin, other_results=other_results, width=40)
    try_and_print(message='PuTTY...', function=update_putty, other_results=other_results, width=40)
    try_and_print(message='Notepad++...', function=update_notepadplusplus, other_results=other_results, width=40)
    try_and_print(message='WizTree...', function=update_wiztree, other_results=other_results, width=40)
    try_and_print(message='XMPlay...', function=update_xmplay, other_results=other_results, width=40)

    # Repairs
    print_info('  Repairs')
    try_and_print(message='AdwCleaner...', function=update_adwcleaner, other_results=other_results, width=40)
    try_and_print(message='KVRT...', function=update_kvrt, other_results=other_results, width=40)
    try_and_print(message='RKill...', function=update_rkill, other_results=other_results, width=40)
    try_and_print(message='TDSS Killer...', function=update_tdsskiller, other_results=other_results, width=40)

    # Uninstallers
    print_info('  Uninstallers')
    try_and_print(message='IObit Uninstaller...', function=update_iobit_uninstaller, other_results=other_results, width=40)

    ## Review ##
    print_standard('Please review the results and download/extract any missing items to .cbin')
    pause('Press Enter to compress the .cbin items')

    ## Compress ##
    print_success('Compressing tools')
    print_info('  _Drivers')
    for item in os.scandir(r'{}\_Drivers'.format(global_vars['CBinDir'])):
      if not re.search(r'^(_Drivers|.*7z)$', item.name, re.IGNORECASE):
        try_and_print(
          message='{}...'.format(item.name),
          function=compress_and_remove_item,
          other_results = other_results,
          width=40,
          item = item)
    print_info('  .cbin')
    for item in os.scandir(global_vars['CBinDir']):
      if not re.search(r'^(_Drivers|_include|.*7z)$', item.name, re.IGNORECASE):
        try_and_print(
          message='{}...'.format(item.name),
          function=compress_and_remove_item,
          other_results = other_results,
          width=40,
          item = item)

    ## Search for network Office/QuickBooks installers & add to LAUNCHERS
    print_success('Scanning for network installers')
    scan_for_net_installers(OFFICE_SERVER, 'Office', min_year=2010)
    scan_for_net_installers(QUICKBOOKS_SERVER, 'QuickBooks', min_year=2015)

    ## Generate Launchers
    print_success('Generating launchers')
    for section in sorted(LAUNCHERS.keys()):
      print_info('  {}'.format(section))
      for name, options in sorted(LAUNCHERS[section].items()):
        try_and_print(message=name, function=generate_launcher,
          section=section, name=name, options=options,
          other_results=other_results, width=40)

    # Rename "Copy WizardKit.cmd" (if necessary)
    source = r'{}\Scripts\Copy WizardKit.cmd'.format(global_vars['BinDir'])
    dest = r'{}\Copy {}.cmd'.format(global_vars['BaseDir'], KIT_NAME_FULL)
    if os.path.exists(source):
      try:
        shutil.move(source, dest)
      except Exception:
        print_error('  Failed to rename "{}.cmd" to "{}.cmd"'.format(
          'Copy WizardKit', KIT_NAME_FULL))

    # Done
    print_standard('\nDone.')
    pause("Press Enter to exit...")
    exit_script()
  except SystemExit:
    pass
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
