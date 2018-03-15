# Wizard Kit: Functions - HW Diagnostics

import json

from functions.common import *

# STATIC VARIABLES
ATTRIBUTES = {
    'NVMe': {
        'critical_warning': {'Error': 1},
        'media_errors': {'Error': 1},
        'power_on_hours': {'Warning': 12000, 'Error': 18000, 'Ignore': True},
        'unsafe_shutdowns': {'Warning': 1},
        },
    'SMART': {
        5: {'Error': 1},
        9: {'Warning': 12000, 'Error': 18000, 'Ignore': True},
        10: {'Warning': 1},
        184: {'Error': 1},
        187: {'Warning': 1},
        188: {'Warning': 1},
        197: {'Error': 1},
        198: {'Error': 1},
        201: {'Warning': 1},
        },
    }
TESTS = {
    'Prime95': {
        'Enabled': False,
        'Status':  'Pending',
        },
    'NVMe/SMART': {
        'Enabled': False,
        'Quick':   False,
        'Status': {},
        },
    'badblocks': {
        'Enabled': False,
        'Results': {},
        'Status': {},
        },
    }

def get_smart_details(dev):
    """Get SMART data for dev if possible, returns dict."""
    cmd = 'sudo smartctl --all --json /dev/{}'.format(dev).split()
    result = run_program(cmd, check=False)
    try:
        return json.loads(result.stdout.decode())
    except Exception:
        # Let other sections deal with the missing data
        return {}

def get_status_color(s):
    """Get color based on status, returns str."""
    color = COLORS['CLEAR']
    if s in ['Denied', 'NS', 'OVERRIDE', 'Unknown']:
        color = COLORS['RED']
    elif s in ['Aborted', 'Working', 'Skipped']:
        color = COLORS['YELLOW']
    elif s in ['CS']:
        color = COLORS['GREEN']
    return color

def menu_diags(*args):
    """Main HW-Diagnostic menu."""
    diag_modes = [
        {'Name': 'All tests',
            'Tests': ['Prime95', 'NVMe/SMART', 'badblocks']},
        {'Name': 'Prime95',
            'Tests': ['Prime95']},
        {'Name': 'NVMe/SMART & badblocks',
            'Tests': ['NVMe/SMART', 'badblocks']},
        {'Name': 'NVMe/SMART',
            'Tests': ['NVMe/SMART']},
        {'Name': 'badblocks',
            'Tests': ['badblocks']},
        {'Name': 'Quick drive test',
            'Tests': ['Quick', 'NVMe/SMART']},
        ]
    actions = [
        {'Letter': 'A', 'Name': 'Audio test'},
        {'Letter': 'N', 'Name': 'Network test'},
        {'Letter': 'M', 'Name': 'Screen Saver - Matrix', 'CRLF': True},
        {'Letter': 'P', 'Name': 'Screen Saver - Pipes'},
        {'Letter': 'Q', 'Name': 'Quit', 'CRLF': True},
        ]

    # CLI-mode actions
    if 'DISPLAY' not in global_vars['Env']:
        actions.extend([
            {'Letter': 'R', 'Name': 'Reboot', 'CRLF': True},
            {'Letter': 'S', 'Name': 'Shutdown'},
            ])

    # Quick disk check
    if 'quick' in args:
        run_tests(['Quick', 'NVMe/SMART'])
        exit_script()

    # Show menu
    while True:
        selection = menu_select(
            title = 'Hardware Diagnostics: Menu',
            main_entries = diag_modes,
            action_entries = actions,
            spacer = '──────────────────────────')
        if selection.isnumeric():
            if diag_modes[int(selection)-1]['Name'] != 'Quick drive test':
                # Save log for non-quick tests
                ticket_number = get_ticket_number()
                global_vars['LogDir'] = '{}/Tickets/{}'.format(
                    global_vars['Env']['HOME'],
                    ticket_number)
                os.makedirs(global_vars['LogDir'], exist_ok=True)
                global_vars['LogFile'] = '{}/Hardware Diagnostics.log'.format(
                    global_vars['LogDir'])
            run_tests(diag_modes[int(selection)-1]['Tests'])
        elif selection == 'A':
            run_program(['hw-diags-audio'], check=False, pipe=False)
            pause('Press Enter to return to main menu... ')
        elif selection == 'N':
            run_program(['hw-diags-network'], check=False, pipe=False)
            pause('Press Enter to return to main menu... ')
        elif selection == 'M':
            run_program(['cmatrix', '-abs'], check=False, pipe=False)
        elif selection == 'P':
            run_program(
                'pipes -t 0 -t 1 -t 2 -t 3 -p 5 -R -r 4000'.split(),
                check=False, pipe=False)
        elif selection == 'R':
            run_program(['reboot'])
        elif selection == 'S':
            run_program(['poweroff'])
        elif selection == 'Q':
            break

def run_badblocks():
    """Run a read-only test for all detected disks."""
    aborted = False
    clear_screen()
    print_log('\nStart badblocks test(s)\n')
    progress_file = '{}/badblocks_progress.out'.format(global_vars['LogDir'])
    update_progress()

    # Set Window layout and start test
    run_program('tmux split-window -dhl 15 watch -c -n1 -t cat {}'.format(
        TESTS['Progress Out']).split())

    # Show disk details
    for name, dev in sorted(TESTS['badblocks']['Devices'].items()):
        show_disk_details(dev)
        print_standard(' ')
    update_progress()

    # Run
    print_standard('Running badblock test(s):')
    for name, dev in sorted(TESTS['badblocks']['Devices'].items()):
        cur_status = TESTS['badblocks']['Status'][name]
        nvme_smart_status = TESTS['NVMe/SMART']['Status'].get(name, None)
        if cur_status == 'Denied':
            # Skip denied disks
            continue
        if nvme_smart_status == 'NS':
            TESTS['badblocks']['Status'][name] = 'Skipped'
        else:
            # Not testing SMART, SMART CS, or SMART OVERRIDE
            TESTS['badblocks']['Status'][name] = 'Working'
            update_progress()
            print_standard('  /dev/{:11}  '.format(name+'...'), end='', flush=True)
            run_program('tmux split-window -dl 5 {} {} {}'.format(
                'hw-diags-badblocks',
                '/dev/{}'.format(name),
                progress_file).split())
            wait_for_process('badblocks')
            print_standard('Done', timestamp=False)

            # Check results
            with open(progress_file, 'r') as f:
                text = f.read()
                TESTS['badblocks']['Results'][name] = text
                r = re.search(r'Pass completed.*0/0/0 errors', text)
                if r:
                    TESTS['badblocks']['Status'][name] = 'CS'
                else:
                    TESTS['badblocks']['Status'][name] = 'NS'

            # Move temp file
            shutil.move(progress_file, '{}/badblocks-{}.log'.format(
                global_vars['LogDir'], name))
        update_progress()

    # Done
    run_program('tmux kill-pane -a'.split(), check=False)
    pass

def run_mprime():
    """Run Prime95 for MPRIME_LIMIT minutes while showing the temps."""
    aborted = False
    clear_screen()
    print_log('\nStart Prime95 test')
    TESTS['Prime95']['Status'] = 'Working'
    update_progress()

    # Set Window layout and start test
    run_program('tmux split-window -dl 10 -c {wd} {cmd} {wd}'.format(
        wd=global_vars['TmpDir'], cmd='hw-diags-prime95').split())
    run_program('tmux split-window -dhl 15 watch -c -n1 -t cat {}'.format(
        TESTS['Progress Out']).split())
    run_program('tmux split-window -bd watch -c -n1 -t hw-sensors'.split())
    run_program('tmux resize-pane -y 3'.split())
    
    # Start test
    run_program(['apple-fans', 'max'])
    print_standard('Running Prime95 for {} minutes'.format(MPRIME_LIMIT))
    print_warning('If running too hot, press CTL+c to abort the test')
    try:
        sleep(int(MPRIME_LIMIT)*60)
    except KeyboardInterrupt:
        # Catch CTL+C
        aborted = True

    # Save "final" temps
    run_program(
        cmd = 'hw-sensors >> "{}/Final Temps.out"'.format(
            global_vars['LogDir']).split(),
        check = False,
        pipe = False,
        shell = True)
    run_program(
        cmd = 'hw-sensors --nocolor >> "{}/Final Temps.log"'.format(
            global_vars['LogDir']).split(),
        check = False,
        pipe = False,
        shell = True)

    # Stop test
    run_program('killall -s INT mprime'.split(), check=False)
    run_program(['apple-fans', 'auto'])

    # Move logs to Ticket folder
    for item in os.scandir(global_vars['TmpDir']):
        try:
            shutil.move(item.path, global_vars['LogDir'])
        except Exception:
            print_error('ERROR: Failed to move "{}" to "{}"'.format(
                item.path,
                global_vars['LogDir']))

    # Check logs
    TESTS['Prime95']['NS'] = False
    TESTS['Prime95']['CS'] = False
    log = '{}/results.txt'.format(global_vars['LogDir'])
    if os.path.exists(log):
        with open(log, 'r') as f:
            text = f.read()
            TESTS['Prime95']['results.txt'] = text
            r = re.search(r'(error|fail)', text)
            TESTS['Prime95']['NS'] = bool(r)
    log = '{}/prime.log'.format(global_vars['LogDir'])
    if os.path.exists(log):
        with open(log, 'r') as f:
            text = f.read()
            TESTS['Prime95']['prime.log'] = text
            r = re.search(r'completed.*0 errors, 0 warnings', text)
            TESTS['Prime95']['CS'] = bool(r)

    # Update status
    if aborted:
        TESTS['Prime95']['Status'] = 'Aborted'
        print_warning('\nAborted.')
        update_progress()
        if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled']:
            if not ask('Proceed to next test?'):
                run_program('tmux kill-pane -a'.split())
                raise GenericError
    else:
        if TESTS['Prime95']['NS']:
            TESTS['Prime95']['Status'] = 'NS'
        elif TESTS['Prime95']['CS']:
            TESTS['Prime95']['Status'] = 'CS'
        else:
            TESTS['Prime95']['Status'] = 'Unknown'
    update_progress()

    # Done
    run_program('tmux kill-pane -a'.split())

def run_nvme_smart():
    """Run the built-in NVMe or SMART test for all detected disks."""
    aborted = False
    clear_screen()
    print_log('\nStart NVMe/SMART test(s)\n')
    progress_file = '{}/selftest_progress.out'.format(global_vars['LogDir'])
    update_progress()

    # Set Window layout and start test
    run_program('tmux split-window -dl 3 watch -c -n1 -t cat {}'.format(
        progress_file).split())
    run_program('tmux split-window -dhl 15 watch -c -n1 -t cat {}'.format(
        TESTS['Progress Out']).split())

    # Show disk details
    for name, dev in sorted(TESTS['NVMe/SMART']['Devices'].items()):
        show_disk_details(dev)
        print_standard(' ')
    update_progress()

    # Run
    for name, dev in sorted(TESTS['NVMe/SMART']['Devices'].items()):
        cur_status = TESTS['NVMe/SMART']['Status'][name]
        if cur_status == 'OVERRIDE':
            # Skipping test per user request
            continue
        if TESTS['NVMe/SMART']['Quick'] or dev.get('NVMe Disk', False):
            # Skip SMART self-tests for quick checks and NVMe disks
            if dev['Quick Health OK']:
                TESTS['NVMe/SMART']['Status'][name] = 'CS'
            else:
                TESTS['NVMe/SMART']['Status'][name] = 'NS'
        elif not dev['Quick Health OK']:
            # SMART overall == Failed or attributes bad, avoid self-test
            TESTS['NVMe/SMART']['Status'][name] = 'NS'
        else:
            # Start SMART short self-test
            test_length = dev['smartctl'].get(
                'ata_smart_data', {}).get(
                'self_test', {}).get(
                'polling_minutes', {}).get(
                'short', 5)
            test_length = int(test_length) + 5
            TESTS['NVMe/SMART']['Status'][name] = 'Working'
            update_progress()
            print_standard('Running SMART short self-test(s):')
            print_standard(
                '  /dev/{:8}({} minutes)...  '.format(name, test_length),
                end='', flush=True)
            run_program(
                'sudo smartctl -t short /dev/{}'.format(name).split(),
                check=False)
            
            # Wait and show progress (in 10 second increments)
            for iteration in range(int(test_length*60/10)):
                # Update SMART data
                dev['smartctl'] = get_smart_details(name)

                # Check if test is complete
                if iteration >= 6:
                    done = dev['smartctl'].get(
                        'ata_smart_data', {}).get(
                        'self_test', {}).get(
                        'status', {}).get(
                        'passed', False)
                    if done:
                        break

                # Update progress_file
                with open(progress_file, 'w') as f:
                    f.write('SMART self-test status:\n  {}'.format(
                        dev['smartctl'].get(
                            'ata_smart_data', {}).get(
                            'self_test', {}).get(
                            'status', {}).get(
                            'string', 'unknown')))
                sleep(10)
            os.remove(progress_file)

            # Check result
            test_passed = dev['smartctl'].get(
                'ata_smart_data', {}).get(
                'self_test', {}).get(
                'status', {}).get(
                'passed', False)
            if test_passed:
                TESTS['NVMe/SMART']['Status'][name] = 'CS'
            else:
                TESTS['NVMe/SMART']['Status'][name] = 'NS'
            update_progress()
            print_standard('Done', timestamp=False)

    # Done
    run_program('tmux kill-pane -a'.split(), check=False)

def run_tests(tests):
    """Run selected hardware test(s)."""
    print_log('Starting Hardware Diagnostics')
    print_log('\nRunning tests: {}'.format(', '.join(tests)))
    # Enable selected tests
    for t in ['Prime95', 'NVMe/SMART', 'badblocks']:
        TESTS[t]['Enabled'] = t in tests
    TESTS['NVMe/SMART']['Quick'] = 'Quick' in tests

    # Initialize
    if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled']:
        scan_disks()
    update_progress()

    # Run
    mprime_aborted = False
    if TESTS['Prime95']['Enabled']:
        try:
            run_mprime()
        except GenericError:
            mprime_aborted = True
    if not mprime_aborted:
        if TESTS['NVMe/SMART']['Enabled']:
            run_nvme_smart()
        if TESTS['badblocks']['Enabled']:
            run_badblocks()
    
    # Show results
    show_results()

    # Open log
    if not TESTS['NVMe/SMART']['Quick']:
        try:
            popen_program(['nohup', 'leafpad', global_vars['LogFile']])
        except Exception:
            print_error('ERROR: Failed to open log: {}'.format(
                global_vars['LogFile']))
            pause('Press Enter to exit...')

def scan_disks():
    """Scan for disks eligible for hardware testing."""
    clear_screen()

    # Get eligible disk list
    result = run_program(['lsblk', '-J', '-O'])
    json_data = json.loads(result.stdout.decode())
    devs = {}
    for d in json_data.get('blockdevices', []):
        if d['type'] == 'disk':
            if d['hotplug'] == '0':
                devs[d['name']] = {'lsblk': d}
                TESTS['NVMe/SMART']['Status'][d['name']] = 'Pending'
                TESTS['badblocks']['Status'][d['name']] = 'Pending'
            else:
                # Skip WizardKit devices
                wk_label = '{}_LINUX'.format(KIT_NAME_SHORT)
                if wk_label not in [c.get('label', '') for c in d.get('children', [])]:
                    devs[d['name']] = {'lsblk': d}
                    TESTS['NVMe/SMART']['Status'][d['name']] = 'Pending'
                    TESTS['badblocks']['Status'][d['name']] = 'Pending'
    
    for dev, data in devs.items():
        # Get SMART attributes
        run_program(
            cmd = 'sudo smartctl -s on /dev/{}'.format(dev).split(),
            check = False)
        data['smartctl'] = get_smart_details(dev)
    
        # Get NVMe attributes
        if data['lsblk']['tran'] == 'nvme':
            cmd = 'sudo nvme smart-log /dev/{} -o json'.format(dev).split()
            result = run_program(cmd, check=False)
            try:
                data['nvme-cli'] = json.loads(result.stdout.decode())
            except Exception:
                # Let other sections deal with the missing data
                data['nvme-cli'] = {}
            data['NVMe Disk'] = True

        # Set "Quick Health OK" value
        ## NOTE: If False then require override for badblocks test
        wanted_smart_list = [
            'ata_smart_attributes',
            'ata_smart_data',
            'smart_status',
            ]
        if data.get('NVMe Disk', False):
            crit_warn = data['nvme-cli'].get('critical_warning', 1)
            data['Quick Health OK'] = True if crit_warn == 0 else False
        elif set(wanted_smart_list).issubset(data['smartctl'].keys()):
            data['SMART Pass'] = data['smartctl'].get('smart_status', {}).get(
                'passed', False)
            data['Quick Health OK'] = data['SMART Pass']
            data['SMART Support'] = True
        else:
            data['Quick Health OK'] = False
            data['SMART Support'] = False
            
        # Ask for manual overrides if necessary
        if not data['Quick Health OK'] and TESTS['badblocks']['Enabled']:
            show_disk_details(data)
            print_warning("WARNING: Health can't be confirmed for: {}".format(
                '/dev/{}'.format(dev)))
            dev_name = data['lsblk']['name']
            print_standard(' ')
            if ask('Run badblocks for this device anyway?'):
                TESTS['NVMe/SMART']['Status'][dev_name] = 'OVERRIDE'
            else:
                TESTS['NVMe/SMART']['Status'][dev_name] = 'NS'
                TESTS['badblocks']['Status'][dev_name] = 'Denied'
            print_standard(' ') # In case there's more than one "OVERRIDE" disk

    TESTS['NVMe/SMART']['Devices'] = devs
    TESTS['badblocks']['Devices'] = devs

def show_disk_details(dev):
    """Display disk details."""
    dev_name = dev['lsblk']['name']
    # Device description
    print_info('Device: /dev/{}'.format(dev['lsblk']['name']))
    print_standard(' {:>4} ({}) {} {}'.format(
        str(dev['lsblk'].get('size', '???b')).strip(),
        str(dev['lsblk'].get('tran', '???')).strip().upper().replace(
            'NVME', 'NVMe'),
        str(dev['lsblk'].get('model', 'Unknown Model')).strip(),
        str(dev['lsblk'].get('serial', 'Unknown Serial')).strip(),
        ))

    # Warnings
    if dev.get('NVMe Disk', False):
        if dev['Quick Health OK']:
            print_warning('WARNING: NVMe support is still experimental')
        else:
            print_error('ERROR: NVMe disk is reporting critical warnings')
    elif not dev['SMART Support']:
        print_error('ERROR: Unable to retrieve SMART data')
    elif not dev['SMART Pass']:
        print_error('ERROR: SMART overall-health assessment result: FAILED')

    # Attributes
    if dev.get('NVMe Disk', False):
        print_info('Attributes:')
        for attrib, threshold in sorted(ATTRIBUTES['NVMe'].items()):
            if attrib in dev['nvme-cli']:
                print_standard(
                    '  {:37}'.format(attrib.replace('_', ' ').title()),
                    end='', flush=True)
                raw_num = dev['nvme-cli'][attrib]
                raw_str = str(raw_num)
                if (threshold.get('Error', False) and
                    raw_num >= threshold.get('Error', -1)):
                    print_error(raw_str, timestamp=False)
                    if not threshold.get('Ignore', False):
                        dev['Quick Health OK'] = False
                        TESTS['NVMe/SMART']['Status'][dev_name] = 'NS'
                elif (threshold.get('Warning', False) and
                    raw_num >= threshold.get('Warning', -1)):
                    print_warning(raw_str, timestamp=False)
                else:
                    print_success(raw_str, timestamp=False)
    elif dev['smartctl'].get('ata_smart_attributes', None):
        # SMART attributes
        print_info('Attributes:')
        s_table = dev['smartctl'].get('ata_smart_attributes', {}).get(
            'table', {})
        s_table = {a.get('id', 'Unknown'): a for a in s_table}
        for attrib, threshold in sorted(ATTRIBUTES['SMART'].items()):
            if attrib in s_table:
                print_standard(
                    '  {:>3}  {:32}'.format(
                        attrib,
                        s_table[attrib]['name']).replace('_', ' ').title(),
                    end='', flush=True)
                raw_str = s_table[attrib]['raw']['string']
                raw_num = re.sub(r'^(\d+).*$', r'\1', raw_str)
                try:
                    raw_num = float(raw_num)
                except ValueError:
                    # Not sure about this one, print raw_str without color?
                    print_standard(raw_str, timestamp=False)
                    continue
                if (threshold.get('Error', False) and
                    raw_num >= threshold.get('Error', -1)):
                    print_error(raw_str, timestamp=False)
                    if not threshold.get('Ignore', False):
                        dev['Quick Health OK'] = False
                        TESTS['NVMe/SMART']['Status'][dev_name] = 'NS'
                elif (threshold.get('Warning', False) and
                    raw_num >= threshold.get('Warning', -1)):
                    print_warning(raw_str, timestamp=False)
                else:
                    print_success(raw_str, timestamp=False)

def show_results():
    """Show results for selected test(s)."""
    clear_screen()
    print_log('\n───────────────────────────')
    print_standard('Hardware Diagnostic Results')
    update_progress()

    # Set Window layout and show progress
    run_program('tmux split-window -dhl 15 watch -c -n1 -t cat {}'.format(
        TESTS['Progress Out']).split())

    # Prime95
    if TESTS['Prime95']['Enabled']:
        print_success('\nPrime95:')
        for log, regex in [
            ['results.txt', r'(error|fail)'],
            ['prime.log', r'completed.*0 errors, 0 warnings']]:
            if log in TESTS['Prime95']:
                print_info('Log: {}'.format(log))
                lines = [line.strip() for line
                    in TESTS['Prime95'][log].splitlines()
                    if re.search(regex, line, re.IGNORECASE)]
                for line in lines[-4:]:
                    line = re.sub(r'^.*Worker #\d.*Torture Test (.*)', r'\1', 
                        line, re.IGNORECASE)
                    if TESTS['Prime95'].get('NS', False):
                        print_error('  {}'.format(line))
                    else:
                        print_standard('  {}'.format(line))
        print_info('Final temps')
        print_log('  See Final Temps.log')
        with open('{}/Final Temps.out'.format(global_vars['LogDir']), 'r') as f:
            for line in f.readlines():
                if re.search(r'^\s*$', line.strip()):
                    # Stop after coretemps (which should be first)
                    break
                print('  {}'.format(line.strip()))
        print_standard(' ')

    # NVMe/SMART / badblocks
    if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled']:
        print_success('Disks:')
        for name, dev in sorted(TESTS['NVMe/SMART']['Devices'].items()):
            show_disk_details(dev)
            bb_status = TESTS['badblocks']['Status'].get(name, None)
            if (TESTS['badblocks']['Enabled']
                and bb_status not in ['Denied', 'OVERRIDE', 'Skipped']):
                print_info('badblocks:')
                result = TESTS['badblocks']['Results'].get(name, '')
                for line in result.splitlines():
                    if re.search(r'Pass completed', line, re.IGNORECASE):
                        line = re.sub(
                            r'Pass completed,?\s+', r'',
                            line.strip(), re.IGNORECASE)
                        if TESTS['badblocks']['Status'][name] == 'CS':
                            print_standard('  {}'.format(line))
                        else:
                            print_error('  {}'.format(line))
            print_standard(' ')

    # Done
    pause('Press Enter to return to main menu... ')
    run_program('tmux kill-pane -a'.split())

def update_progress():
    """Update progress file."""
    if 'Progress Out' not in TESTS:
        TESTS['Progress Out'] = '{}/progress.out'.format(global_vars['LogDir'])
    output = []
    output.append('{BLUE}HW  Diagnostics{CLEAR}'.format(**COLORS))
    output.append('───────────────')
    if TESTS['Prime95']['Enabled']:
        output.append(' ')
        output.append('{BLUE}Prime95{s_color}{status:>8}{CLEAR}'.format(
            s_color = get_status_color(TESTS['Prime95']['Status']),
            status = TESTS['Prime95']['Status'],
            **COLORS))
    if TESTS['NVMe/SMART']['Enabled']:
        output.append(' ')
        output.append('{BLUE}NVMe / SMART{CLEAR}'.format(**COLORS))
        if TESTS['NVMe/SMART']['Quick']:
            output.append('{YELLOW} (Quick Check){CLEAR}'.format(**COLORS))
        for dev, status in sorted(TESTS['NVMe/SMART']['Status'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 15-len(dev),
                s_color = get_status_color(status),
                status = status,
                **COLORS))
    if TESTS['badblocks']['Enabled']:
        output.append(' ')
        output.append('{BLUE}badblocks{CLEAR}'.format(**COLORS))
        for dev, status in sorted(TESTS['badblocks']['Status'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 15-len(dev),
                s_color = get_status_color(status),
                status = status,
                **COLORS))

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(TESTS['Progress Out'], 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

