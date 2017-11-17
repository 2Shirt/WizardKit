# Wizard Kit: DISM wrapper

import os
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: DISM helper Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
os.makedirs('{LogDir}'.format(**vars_wk), exist_ok=True)
vars_wk['LogFile'] = '{LogDir}\\dism_helper.log'.format(**vars_wk)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

def exit_script():
    pause("Press Enter to exit...")
    quit()

def check_health():
    _args = [
        '/Online',
        '/Cleanup-Image',
        '/CheckHealth',
        '/LogPath:{LogDir}\\DISM_CheckHealth.log'.format(**vars_wk)]
    try:
        _result = run_program('dism', _args).stdout.decode()
    except subprocess.CalledProcessError:
        print_error('ERROR: failed to run DISM health check', vars_wk['LogFile'])
        _result = ['Unknown']
    else:
        # Check result
        if re.search(r'No component store corruption detected', _result, re.IGNORECASE):
            return True
        else:
            for line in _result:
                line = '  ' + line
                print_warning(line, vars_wk['LogFile'])
            print_error('ERROR: DISM encountered errors, please review details above', vars_wk['LogFile'])
    return False

def restore_health():
    _args = [
        '/Online',
        '/Cleanup-Image',
        '/RestoreHealth',
        '/LogPath:{LogDir}\\DISM_RestoreHealth.log'.format(**vars_wk),
        '-new_console:n',
        '-new_console:s33V']
    run_program('dism', _args, pipe=False, check=False)
    wait_for_process('dism')

def scan_health():
    _args = [
        '/Online',
        '/Cleanup-Image',
        '/ScanHealth',
        '/LogPath:{LogDir}\\DISM_ScanHealth.log'.format(**vars_wk),
        '-new_console:n',
        '-new_console:s33V']
    run_program('dism', _args, pipe=False, check=False)
    wait_for_process('dism')

if __name__ == '__main__':
    stay_awake(vars_wk)
    if vars_wk['Version'] in ['8', '10']:
        options = [
            {'Name': 'Check Health', 'Command': 'Check'},
            {'Name': 'Restore Health', 'Command': 'Restore'}]
        actions = [{'Name': 'Quit', 'Letter': 'Q'}]
        selection = menu_select('Please select action to perform', options, actions)
        run_program('cls', check=False, pipe=False, shell=True)
        if selection == 'Q':
            abort()
        elif options[int(selection)-1]['Command'] == 'Check':
            print_info('Scanning for component store corruption...', vars_wk['LogFile'])
            scan_health()
            if check_health():
                print_success('No component store corruption detected.', vars_wk['LogFile'])
        elif options[int(selection)-1]['Command'] == 'Restore':
            print_info('Scanning for, and attempting to repair, component store corruption...', vars_wk['LogFile'])
            restore_health()
            if check_health():
                print_success('No component store corruption detected.', vars_wk['LogFile'])
        else:
            abort()
    else:
        # Windows 7 and older
        print_error('ERROR: This tool is not intended for {ProductName}.'.format(**vars_wk), vars_wk['LogFile'])
    
    print_success('Done.', vars_wk['LogFile'])
    kill_process('caffeine.exe')
    exit_script()
