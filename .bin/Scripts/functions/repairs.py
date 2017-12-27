# Wizard Kit: Functions - Repairs

from functions.common import *

def run_chkdsk(repair=False):
    """Run CHKDSK scan or schedule offline repairs."""
    if repair:
        run_chkdsk_offline()
    else:
        run_chkdsk_scan()

def run_chkdsk_scan():
    """Run CHKDSK in a "split window" and report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        cmd = ['chkdsk', global_vars['Env']['SYSTEMDRIVE'], '/scan', '/perf']
    else:
        cmd = ['chkdsk', global_vars['Env']['SYSTEMDRIVE']]
    out = run_program(cmd, check=False)
    # retcode == 0: no issues
    # retcode == 1: fixed issues (also happens when chkdsk.exe is killed?)
    # retcode == 2: issues
    if int(out.returncode) > 0:
        # print_error('  ERROR: CHKDSK encountered errors')
        raise GenericError

    # Save stderr
    with open(r'{LogDir}\CHKDSK.err'.format(**global_vars), 'a') as f:
        for line in out.stderr.decode().splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open(r'{LogDir}\CHKDSK.log'.format(**global_vars), 'a') as f:
        for line in out.stdout.decode().splitlines():
            f.write(line.strip() + '\n')

def run_chkdsk_offline():
    """Set filesystem 'dirty bit' to force a chkdsk during next boot."""
    cmd = [
        'fsutil', 'dirty',
        'set',
        global_vars['Env']['SYSTEMDRIVE']]
    out = run_program(cmd, check=False)
    if int(out.returncode) > 0:
        raise GenericError

def run_dism(repair=False):
    """Run DISM /RestoreHealth, then /CheckHealth, and then report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        if repair:
            # Restore Health
            cmd = [
                'DISM', '/Online',
                '/Cleanup-Image', '/RestoreHealth',
                r'/LogPath:"{LogDir}\DISM_RestoreHealth.log"'.format(
                    **global_vars),
                '-new_console:n', '-new_console:s33V']
        else:
            # Scan Health
            cmd = [
                'DISM', '/Online',
                '/Cleanup-Image', '/ScanHealth',
                r'/LogPath:"{LogDir}\DISM_ScanHealth.log"'.format(
                    **global_vars),
                '-new_console:n', '-new_console:s33V']
        run_program(cmd, pipe=False, check=False, shell=True)
        wait_for_process('dism')
        # Now check health
        cmd = [
            'DISM', '/Online',
            '/Cleanup-Image', '/CheckHealth',
            r'/LogPath:"{LogDir}\DISM_CheckHealth.log"'.format(**global_vars)]
        result = run_program(cmd, shell=True).stdout.decode()
        # Check result
        if 'no component store corruption detected' not in result.lower():
            raise GenericError
    else:
        raise UnsupportedOSError

def run_kvrt():
    """Run KVRT."""
    extract_item('KVRT', silent=True)
    os.makedirs(global_vars['QuarantineDir'], exist_ok=True)
    cmd = [
        global_vars['Tools']['KVRT'],
        '-accepteula', '-dontcryptsupportinfo', '-fixednames',
        '-d', global_vars['QuarantineDir'],
        '-processlevel', '3']
    popen_program(cmd, pipe=False)

def run_sfc_scan():
    """Run SFC in a "split window" and report errors."""
    cmd = [
        r'{SYSTEMROOT}\System32\sfc.exe'.format(**global_vars['Env']),
        '/scannow']
    out = run_program(cmd, check=False)
    # Save stderr
    with open(r'{LogDir}\SFC.err'.format(**global_vars), 'a') as f:
        for line in out.stderr.decode('utf-8', 'ignore').splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open(r'{LogDir}\SFC.log'.format(**global_vars), 'a') as f:
        for line in out.stdout.decode('utf-8', 'ignore').splitlines():
            f.write(line.strip() + '\n')
    # Check result
    log_text = out.stdout.decode('utf-8', 'ignore').replace('\0', '')
    if re.findall(r'did\s+not\s+find\s+any\s+integrity\s+violations', log_text):
        pass
    elif re.findall(r'successfully\s+repaired\s+them', log_text):
        raise GenericRepair
    else:
        raise GenericError

def run_tdsskiller():
    """Run TDSSKiller."""
    extract_item('TDSSKiller', silent=True)
    os.makedirs(r'{QuarantineDir}\TDSSKiller'.format(
        **global_vars), exist_ok=True)
    cmd = [
        global_vars['Tools']['TDSSKiller'],
        '-l', r'{LogDir}\TDSSKiller.log'.format(**global_vars),
        '-qpath', r'{QuarantineDir}\TDSSKiller'.format(**global_vars),
        '-accepteula', '-accepteulaksn',
        '-dcexact', '-tdlfs']
    run_program(cmd, pipe=False)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
