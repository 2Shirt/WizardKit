# Wizard Kit: Functions - HW Diagnostics

import libtmux
import json

from functions.common import *

# STATIC VARIABLES
TMUX = libtmux.Server()
SESSION = TMUX.find_where({'session_name': 'hw-diags'})
WINDOW = SESSION.windows[0] # Should be a safe assumption
PANE = WINDOW.panes[0]      # Should be a safe assumption
TESTS = {
    'Prime95': {
        'Enabled': False,
        'Status':  'Pending',
        },
    'SMART': {
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
    elif s in ['Working', 'Skipped']:
        color = COLORS['YELLOW']
    elif s in ['CS']:
        color = COLORS['GREEN']
    return color

def menu_diags():
    diag_modes = [
        {'Name': 'All tests', 'Tests': ['Prime95', 'SMART', 'badblocks']},
        {'Name': 'Prime95', 'Tests': ['Prime95']},
        {'Name': 'SMART & badblocks', 'Tests': ['SMART', 'badblocks']},
        {'Name': 'SMART', 'Tests': ['SMART']},
        {'Name': 'badblocks', 'Tests': ['badblocks']},
        {'Name': 'Quick drive test', 'Tests': ['Quick', 'SMART']},
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
            spacer = '─────────────────────────')
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
    # Set Window layout
    window = SESSION.new_window()
    pane_sensors = window.panes[0]
    pane_mprime = window.split_window(attach=False)
    pane_mprime.set_height(10)
    pane_progress = window.split_window(attach=False, vertical=False)
    pane_progress.set_width(16)
    
    # Start test
    run_program(['apple-fans', 'max'])
    pane_sensors.send_keys('watch -c -n1 -t hw-sensors')
    pane_progress.send_keys('watch -c -n1 -t cat "{}"'.format(TESTS['Progress Out']))
    pane_mprime.send_keys('mprime -t')
    #sleep(MPRIME_LIMIT*60)
    sleep(15)

    # Done
    run_program(['apple-fans', 'auto'])
    window.kill_window()

def run_smart():
    # Set Window layout
    window = SESSION.new_window()
    pane_sensors = window.panes[0]
    pane_smart = window.split_window(attach=False)
    pane_smart.set_height(10)
    pane_progress = window.split_window(attach=False, vertical=False)
    pane_progress.set_width(16)
    
    # Start test
    run_program(['apple-fans', 'max'])
    pane_sensors.send_keys('watch -c -n1 -t hw-sensors')
    pane_progress.send_keys('watch -c -n1 -t cat "{}"'.format(TESTS['Progress Out']))
    pane_mprime.send_keys('mprime -t')
    #sleep(MPRIME_LIMIT*60)
    sleep(15)

    # Done
    run_program(['apple-fans', 'auto'])
    window.kill_window()

def run_tests(tests):
    # Enable selected tests
    for t in ['Prime95', 'SMART', 'badblocks']:
        TESTS[t]['Enabled'] = t in tests
    TESTS['SMART']['Quick'] = 'Quick' in tests

    # Initialize
    if TESTS['SMART']['Enabled'] or TESTS['badblocks']['Enabled']:
        scan_disks()
    update_progress()

    # Run
    if TESTS['Prime95']['Enabled']:
        run_mprime()
    if TESTS['SMART']['Enabled']:
        run_smart()
    if TESTS['badblocks']['Enabled']:
        run_badblocks()

def scan_disks():
    clear_screen()
    
    # Get eligible disk list
    cmd = 'lsblk -J -o HOTPLUG,NAME,TRAN,TYPE'.split()
    result = run_program(cmd)
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

        # Set "Health OK" value
        ## NOTE: OK == we'll check the SMART/NVMe attributes, else req override
        wanted_smart_list = [
            'ata_smart_attributes',
            'ata_smart_data',
            'smart_status',
            ]
        if data['lsblk']['tran'] == 'nvme':
            crit_warn = data['nvme-cli'].get('critical_warning', 1)
            data['Health OK'] = True if crit_warn == 0 else False
        elif set(wanted_smart_list).issubset(data['smartctl'].keys()):
            data['Health OK'] = data.get(
                'smart_status', {}).get('passed', False)
        else:
            data['Health OK'] = False
            
        # Ask for manual overrides if necessary
        if not data['Health OK'] and TESTS['badblocks']['Enabled']:
            #TODO Print disk "report" for reference
            print_warning("WARNING: Health can't be confirmed for: {}".format(
                '/dev/{}'.format(dev)))
            if ask('Run badblocks for this device anyway?'):
                data['OVERRIDE'] = True

    TESTS['SMART']['Devices'] = devs
    TESTS['badblocks']['Devices'] = devs

def update_progress():
    if 'Progress Out' not in TESTS:
        TESTS['Progress Out'] = '{}/progress.out'.format(global_vars['LogDir'])
    output = []
    output.append('{BLUE}HW  Diagnostics{CLEAR}'.format(**COLORS))
    output.append('───────────────')
    if TESTS['Prime95']['Enabled']:
        output.append('{BLUE}Prime95{s_color}{status:>8}{CLEAR}'.format(
            s_color = get_status_color(TESTS['Prime95']['Status']),
            status = TESTS['Prime95']['Status'],
            **COLORS))
    if TESTS['SMART']['Enabled']:
        output.append('{BLUE}SMART{CLEAR}'.format(**COLORS))
        for dev, data in sorted(TESTS['SMART']['Devices'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 16-len(dev),
                s_color = get_status_color(status),
                status = data['Status'],
                **COLORS))
    if TESTS['badblocks']['Enabled']:
        output.append('{BLUE}badblocks{CLEAR}'.format(**COLORS))
        for dev, data in sorted(TESTS['badblocks']['Devices'].items()):
            output.append('{dev}{s_color}{status:>{pad}}{CLEAR}'.format(
                dev = dev,
                pad = 16-len(dev),
                s_color = get_status_color(data['Status']),
                status = data['Status'],
                **COLORS))

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(TESTS['Progress Out'], 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

