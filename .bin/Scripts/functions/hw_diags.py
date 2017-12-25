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
        },
    'badblocks': {
        'Enabled': False,
        },
    }

def get_smart_details(dev):
    cmd = 'sudo smartctl --all --json /dev/{}'.format(dev).split()
    result = run_program(cmd, check=False)
    try:
        return json.loads(result.stdout.decode())
    except Exception:
        # Let other sections deal with the missing data
        return {}

def get_status_color(s):
    color = COLORS['CLEAR']
    if s in ['NS', 'Unknown']:
        color = COLORS['RED']
    elif s in ['Aborted', 'OVERRIDE', 'Working', 'Skipped']:
        color = COLORS['YELLOW']
    elif s in ['CS']:
        color = COLORS['GREEN']
    return color

def menu_diags():
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

    # Show menu
    while True:
        selection = menu_select(
            title = 'Hardware Diagnostics: Menu',
            main_entries = diag_modes,
            action_entries = actions,
            spacer = '──────────────────────────')
        if selection.isnumeric():
            run_tests(diag_modes[int(selection)-1]['Tests'])
        elif selection == 'A':
            run_program(['hw-diags-audio'], check=False, pipe=False)
            sleep(1)
        elif selection == 'N':
            run_program(['hw-diags-network'], check=False, pipe=False)
            sleep(1)
        elif selection == 'M':
            run_program(['cmatrix', '-abs'], check=False, pipe=False)
        elif selection == 'P':
            run_program(
                'pipes -t 0 -t 1 -t 2 -t 3 -p 5 -R -r 4000'.split(),
                check=False, pipe=False)
        elif selection == 'Q':
            break

def run_badblocks():
    pass

def run_mprime():
    aborted = False
    clear_screen()
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

    # Stop test
    run_program('killall -s INT mprime'.split(), check=False)
    run_program(['apple-fans', 'auto'])

    # Update status
    if aborted:
        TESTS['Prime95']['Status'] = 'Aborted'
        print_warning('\nAborted.')
        sleep(5)
        update_progress()
        pause('Press Enter to return to menu... ')
    else:
        TESTS['Prime95']['Status'] = 'CS'
    update_progress()

    # Done
    run_program('tmux kill-pane -a'.split())

def run_smart():
    # Set Window layout
    pane_worker = WINDOW.split_window(attach=False)
    pane_worker.set_height(10)
    pane_progress = WINDOW.split_window(attach=False, vertical=False)
    pane_progress.set_width(15)
    pane_progress.clear()
    #pane_progress.send_keys('watch -c -n1 -t cat "{}"'.format(TESTS['Progress Out']))
    pane_progress.send_keys(''.format(TESTS['Progress Out']))

    # Start test
    sleep(120)

    # Done
    run_program(['tmux kill-pane -a'.split()], check=False)

def run_tests(tests):
    # Enable selected tests
    for t in ['Prime95', 'NVMe/SMART', 'badblocks']:
        TESTS[t]['Enabled'] = t in tests
    TESTS['NVMe/SMART']['Quick'] = 'Quick' in tests

    # Initialize
    if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled']:
        scan_disks()
    update_progress()

    # Run
    if TESTS['Prime95']['Enabled']:
        run_mprime()
    if TESTS['NVMe/SMART']['Enabled']:
        run_smart()
    if TESTS['badblocks']['Enabled']:
        run_badblocks()

def scan_disks():
    clear_screen()

    # Get eligible disk list
    result = run_program(['lsblk', '-J', '-O'])
    json_data = json.loads(result.stdout.decode())
    devs = json_data.get('blockdevices', [])
    devs = {d['name']: {'lsblk': d, 'Status': 'Pending'} for d in devs
        if d['type'] == 'disk' and d['hotplug'] == '0'}
    
    for dev, data in devs.items():
        # Get SMART attributes
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
            if ask('Run badblocks for this device anyway?'):
                data['OVERRIDE'] = True

    TESTS['NVMe/SMART']['Devices'] = devs
    TESTS['badblocks']['Devices'] = devs

def show_disk_details(dev):
    # Device description
    print_info('Device: /dev/{}'.format(dev['lsblk']['name']))
    for key in ['model', 'size', 'serial']:
        print_standard('  {:8}{}'.format(key, dev['lsblk'].get(key, 'Unknown')))
    if dev['lsblk'].get('tran', 'Unknown') == 'nvme':
        print_standard('  {:8}{}'.format('type', 'NVMe'))
    else:
        print_standard('  {:8}{}'.format(
            'type',
            dev['lsblk'].get('tran', 'Unknown').upper()))

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
    print_info('Attributes:')
    if dev.get('NVMe Disk', False):
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
                        dev['NVMe/SMART']['Status'] = 'NS'
                elif (threshold.get('Warning', False) and
                    raw_num >= threshold.get('Warning', -1)):
                    print_warning(raw_str, timestamp=False)
                else:
                    print_success(raw_str, timestamp=False)
    else:
        # SMART attributes
        s_table = dev['smartctl'].get('ata_smart_attributes', {}).get(
            'table', {})
        s_table = {a.get('id', 'Unknown'): a for a in s_table}
        for attrib, threshold in sorted(ATTRIBUTES['SMART'].items()):
            if attrib in s_table:
                print_standard(
                    '  {:>3}  {:32}'.format(attrib, s_table[attrib]['name']),
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
                        dev['NVMe/SMART']['Status'] = 'NS'
                elif (threshold.get('Warning', False) and
                    raw_num >= threshold.get('Warning', -1)):
                    print_warning(raw_str, timestamp=False)
                else:
                    print_success(raw_str, timestamp=False)

    # Quick Health OK
    print_standard('Quick health assessment: ', end='', flush=True)
    if dev['Quick Health OK']:
        print_success('Passed.\n', timestamp=False)
    else:
        print_error('Failed.\n', timestamp=False)

def update_progress():
    if 'Progress Out' not in TESTS:
        TESTS['Progress Out'] = '{}/progress.out'.format(global_vars['LogDir'])
    output = []
    output.append('{BLUE}HW  Diagnostics{CLEAR}'.format(**COLORS))
    output.append('───────────────')
    if TESTS['Prime95']['Enabled']:
        output.append('')
        output.append('{BLUE}Prime95{s_color}{status:>8}{CLEAR}'.format(
            s_color = get_status_color(TESTS['Prime95']['Status']),
            status = TESTS['Prime95']['Status'],
            **COLORS))
    if TESTS['NVMe/SMART']['Enabled']:
        output.append('')
        output.append('{BLUE}NVMe / SMART{CLEAR}'.format(**COLORS))
        if TESTS['NVMe/SMART']['Quick']:
            output.append('{YELLOW} (Quick Check){CLEAR}'.format(**COLORS))
        for dev, data in sorted(TESTS['NVMe/SMART']['Devices'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 15-len(dev),
                s_color = get_status_color(data['Status']),
                status = data['Status'],
                **COLORS))
    if TESTS['badblocks']['Enabled']:
        output.append('')
        output.append('{BLUE}badblocks{CLEAR}'.format(**COLORS))
        for dev, data in sorted(TESTS['badblocks']['Devices'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 15-len(dev),
                s_color = get_status_color(data['Status']),
                status = data['Status'],
                **COLORS))

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(TESTS['Progress Out'], 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

