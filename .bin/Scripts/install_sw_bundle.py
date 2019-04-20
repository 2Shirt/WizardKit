# Wizard Kit: Install the standard SW bundle based on the OS version

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.setup import *
init_global_vars()
os.system('title {}: SW Bundle Tool'.format(KIT_NAME_FULL))
set_log_file('Install SW Bundle.log')

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    print_info('{}: SW Bundle Tool\n'.format(KIT_NAME_FULL))
    other_results = {
      'Error': {
        'CalledProcessError':   'Unknown Error',
        'FileNotFoundError':  'File not found',
      },
      'Warning': {
        'GenericRepair':    'Repaired',
        'UnsupportedOSError':   'Unsupported OS',
      }}
    answer_extensions = ask('Install Extensions?')
    answer_adobe_reader = ask('Install Adobe Reader?')
    answer_vcr = ask('Install Visual C++ Runtimes?')
    answer_ninite = ask('Install Ninite Bundle?')
    if answer_ninite and global_vars['OS']['Version'] in ['7']:
      # Vista is dead, not going to check for it
      answer_mse = ask('Install MSE?')
    else:
      answer_mse = False

    print_info('Installing Programs')
    if answer_adobe_reader:
      try_and_print(message='Adobe Reader DC...',
        function=install_adobe_reader, other_results=other_results)
    if answer_vcr:
      install_vcredists()
    if answer_ninite:
      result = try_and_print(message='Ninite bundle...',
        function=install_ninite_bundle, cs='Started',
        mse=answer_mse, other_results=other_results)
      for proc in result['Out']:
        # Wait for all processes to finish
        proc.wait()
    if answer_extensions:
      print_info('Installing Extensions')
      try_and_print(message='Classic Shell skin...',
        function=install_classicstart_skin,
        other_results=other_results)
      try_and_print(message='Google Chrome extensions...',
        function=install_chrome_extensions)
      try_and_print(message='Mozilla Firefox extensions...',
        function=install_firefox_extensions,
        other_results=other_results)
    print_standard('\nDone.')
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
