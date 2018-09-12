# Wizard Kit: Functions - HW Diagnostics

import json
import time

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
        196: {'Warning': 1, 'Error': 10, 'Ignore': True},
        197: {'Error': 1},
        198: {'Error': 1},
        199: {'Error': 1, 'Ignore': True},
        201: {'Warning': 1},
        },
    }
IO_VARS = {
    'Block Size': 512*1024,
    'Chunk Size': 16*1024**2,
    'Minimum Dev Size': 8*1024**3,
    'Minimum Test Size': 10*1024**3,
    'Alt Test Size Factor': 0.01,
    'Progress Refresh Rate': 5,
    'Scale 16': [2**(0.6*x)+(16*x) for x in range(1,17)],
    'Scale 32': [2**(0.6*x/2)+(16*x/2) for x in range(1,33)],
    'Threshold Fail': 65*1024**2,
    'Threshold Warn': 135*1024**2,
    'Threshold Great': 750*1024**2,
    'Graph Horizontal': ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'),
    'Graph Horizontal Width': 40,
    'Graph Vertical': (
        '▏',    '▎',    '▍',    '▌',
        '▋',    '▊',    '▉',    '█',
        '█▏',   '█▎',   '█▍',   '█▌',
        '█▋',   '█▊',   '█▉',   '██',
        '██▏',  '██▎',  '██▍',  '██▌',
        '██▋',  '██▊',  '██▉',  '███',
        '███▏', '███▎', '███▍', '███▌',
        '███▋', '███▊', '███▉', '████'),
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
    'iobenchmark': {
        'Enabled': False,
        'Results': {},
        'Status': {},
        },
    }

def generate_horizontal_graph(rates):
    """Generate two-line horizontal graph from rates, returns str."""
    line_top = ''
    line_bottom = ''
    for r in rates:
        step = get_graph_step(r, scale=16)

        # Set color
        r_color = COLORS['CLEAR']
        if r < IO_VARS['Threshold Fail']:
            r_color = COLORS['RED']
        elif r < IO_VARS['Threshold Warn']:
            r_color = COLORS['YELLOW']
        elif r > IO_VARS['Threshold Great']:
            r_color = COLORS['GREEN']

        # Build graph
        if step < 8:
            line_top += ' '
            line_bottom += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step])
        else:
            line_top += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-8])
            line_bottom += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][-1])
    line_top += COLORS['CLEAR']
    line_bottom += COLORS['CLEAR']
    return '{}\n{}'.format(line_top, line_bottom)

def get_graph_step(rate, scale=16):
    """Get graph step based on rate and scale, returns int."""
    m_rate = rate / (1024**2)
    step = 0
    scale_name = 'Scale {}'.format(scale)
    for x in range(scale-1, -1, -1):
        # Iterate over scale backwards
        if m_rate >= IO_VARS[scale_name][x]:
            step = x
            break
    return step

def get_read_rate(s):
    """Get read rate in bytes/s from dd progress output."""
    real_rate = None
    if re.search(r'[KMGT]B/s', s):
        human_rate = re.sub(r'^.*\s+(\d+\.?\d*)\s+(.B)/s\s*$', r'\1 \2', s)
        real_rate = convert_to_bytes(human_rate)
    return real_rate

def get_smart_details(dev):
    """Get SMART data for dev if possible, returns dict."""
    cmd = 'sudo smartctl --all --json {}{}'.format(
        '' if '/dev/' in dev else '/dev/',
        dev).split()
    result = run_program(cmd, check=False)
    try:
        return json.loads(result.stdout.decode())
    except Exception:
        # Let other sections deal with the missing data
        return {}

def get_smart_value(smart_data, smart_id):
    """Get SMART value from table, returns int or None."""
    value = None
    table = smart_data.get('ata_smart_attributes', {}).get('table', [])
    for row in table:
        if str(row.get('id', '?')) == str(smart_id):
            value = row.get('raw', {}).get('value', None)
    return value

def get_status_color(s):
    """Get color based on status, returns str."""
    color = COLORS['CLEAR']
    if s in ['Denied', 'NS', 'OVERRIDE']:
        color = COLORS['RED']
    elif s in ['Aborted', 'Unknown', 'Working', 'Skipped']:
        color = COLORS['YELLOW']
    elif s in ['CS']:
        color = COLORS['GREEN']
    return color

def menu_diags(*args):
    """Main HW-Diagnostic menu."""
    diag_modes = [
        {'Name': 'All tests',
            'Tests': ['Prime95', 'NVMe/SMART', 'badblocks', 'iobenchmark']},
        {'Name': 'Prime95',
            'Tests': ['Prime95']},
        {'Name': 'All drive tests',
            'Tests': ['NVMe/SMART', 'badblocks', 'iobenchmark']},
        {'Name': 'NVMe/SMART',
            'Tests': ['NVMe/SMART']},
        {'Name': 'badblocks',
            'Tests': ['badblocks']},
        {'Name': 'I/O Benchmark',
            'Tests': ['iobenchmark']},
        {'Name': 'Quick drive test',
            'Tests': ['Quick', 'NVMe/SMART']},
        ]
    actions = [
        {'Letter': 'A', 'Name': 'Audio test'},
        {'Letter': 'K', 'Name': 'Keyboard test'},
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
                global_vars['LogDir'] = '{}/Logs/{}'.format(
                    global_vars['Env']['HOME'],
                    ticket_number if ticket_number else global_vars['Date-Time'])
                os.makedirs(global_vars['LogDir'], exist_ok=True)
                global_vars['LogFile'] = '{}/Hardware Diagnostics.log'.format(
                    global_vars['LogDir'])
            run_tests(diag_modes[int(selection)-1]['Tests'])
        elif selection == 'A':
            run_program(['hw-diags-audio'], check=False, pipe=False)
            pause('Press Enter to return to main menu... ')
        elif selection == 'K':
            run_program(['xev', '-event', 'keyboard'], check=False, pipe=False)
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

def run_iobenchmark():
    """Run a read-only test for all detected disks."""
    aborted = False
    clear_screen()
    print_log('\nStart I/O Benchmark test(s)\n')
    progress_file = '{}/iobenchmark_progress.out'.format(global_vars['LogDir'])
    update_progress()

    # Set Window layout and start test
    run_program('tmux split-window -dhl 15 watch -c -n1 -t cat {}'.format(
        TESTS['Progress Out']).split())

    # Show disk details
    for name, dev in sorted(TESTS['iobenchmark']['Devices'].items()):
        show_disk_details(dev)
        print_standard(' ')
    update_progress()

    # Run
    print_standard('Running benchmark test(s):')
    for name, dev in sorted(TESTS['iobenchmark']['Devices'].items()):
        cur_status = TESTS['iobenchmark']['Status'][name]
        nvme_smart_status = TESTS['NVMe/SMART']['Status'].get(name, None)
        bb_status = TESTS['badblocks']['Status'].get(name, None)
        if cur_status == 'Denied':
            # Skip denied disks
            continue
        if nvme_smart_status == 'NS':
            TESTS['iobenchmark']['Status'][name] = 'Skipped'
        elif bb_status in ['NS', 'Skipped']:
            TESTS['iobenchmark']['Status'][name] = 'Skipped'
        else:
            # (SMART tests not run or CS/OVERRIDE)
            #   AND (BADBLOCKS tests not run or CS)
            TESTS['iobenchmark']['Status'][name] = 'Working'
            update_progress()
            print_standard('  /dev/{:11}  '.format(name+'...'), end='', flush=True)

            # Get dev size
            cmd = 'sudo lsblk -bdno size /dev/{}'.format(name)
            try:
                result = run_program(cmd.split())
                dev_size = result.stdout.decode().strip()
                dev_size = int(dev_size)
            except:
                # Failed to get dev size, requires manual testing instead
                TESTS['iobenchmark']['Status'][name] = 'Unknown'
                continue
            if dev_size < IO_VARS['Minimum Dev Size']:
                TESTS['iobenchmark']['Status'][name] = 'Unknown'
                continue

            # Calculate dd values
            ## test_size is the area to be read in bytes
            ##      If the dev is < 10Gb then it's the whole dev
            ##      Otherwise it's the larger of 10Gb or 1% of the dev
            ##
            ## test_chunks is the number of groups of "Chunk Size" in test_size
            ##      This number is reduced to a multiple of the graph width in
            ##      order to allow for the data to be condensed cleanly
            ##
            ## skip_blocks is the number of "Block Size" groups not tested
            ## skip_count is the number of blocks to skip per test_chunk
            ## skip_extra is how often to add an additional skip block
            ##      This is needed to ensure an even testing across the dev
            ##      This is calculated by using the fractional amount left off
            ##      of the skip_count variable
            test_size = min(IO_VARS['Minimum Test Size'], dev_size)
            test_size = max(
                test_size, dev_size*IO_VARS['Alt Test Size Factor'])
            test_chunks = int(test_size // IO_VARS['Chunk Size'])
            test_chunks -= test_chunks % IO_VARS['Graph Horizontal Width']
            test_size = test_chunks * IO_VARS['Chunk Size']
            skip_blocks = int((dev_size - test_size) // IO_VARS['Block Size'])
            skip_count = int((skip_blocks / test_chunks) // 1)
            skip_extra = 0
            try:
                skip_extra = 1 + int(1 / ((skip_blocks / test_chunks) % 1))
            except ZeroDivisionError:
                # skip_extra == 0 is fine
                pass

            # Open dd progress pane after initializing file
            with open(progress_file, 'w') as f:
                f.write('')
            sleep(1)
            cmd = 'tmux split-window -dp 75 -PF #D tail -f {}'.format(
                progress_file)
            result = run_program(cmd.split())
            bottom_pane = result.stdout.decode().strip()

            # Run dd read tests
            offset = 0
            read_rates = []
            for i in range(test_chunks):
                i += 1
                s = skip_count
                c = int(IO_VARS['Chunk Size'] / IO_VARS['Block Size'])
                if skip_extra and i % skip_extra == 0:
                    s += 1
                cmd = 'sudo dd bs={b} skip={s} count={c} if=/dev/{n} of={o}'.format(
                    b=IO_VARS['Block Size'],
                    s=offset+s,
                    c=c,
                    n=name,
                    o='/dev/null')
                result = run_program(cmd.split())
                result_str = result.stderr.decode().replace('\n', '')
                read_rates.append(get_read_rate(result_str))
                if i % IO_VARS['Progress Refresh Rate'] == 0:
                    # Update vertical graph
                    update_io_progress(
                        percent=i/test_chunks*100,
                        rate=read_rates[-1],
                        progress_file=progress_file)
                # Update offset
                offset += s + c
            print_standard('Done', timestamp=False)

            # Close bottom pane
            run_program(['tmux', 'kill-pane', '-t', bottom_pane])

            # Build report
            h_graph_rates = []
            pos = 0
            width = int(test_chunks / IO_VARS['Graph Horizontal Width'])
            for i in range(IO_VARS['Graph Horizontal Width']):
                # Append average rate for WIDTH number of rates to new array
                h_graph_rates.append(sum(read_rates[pos:pos+width])/width)
                pos += width
            report = generate_horizontal_graph(h_graph_rates)
            report += '\nRead speed: {:3.1f} MB/s (Min: {:3.1f}, Max: {:3.1f})'.format(
                sum(read_rates)/len(read_rates)/(1024**2),
                min(read_rates)/(1024**2),
                max(read_rates)/(1024**2))
            TESTS['iobenchmark']['Results'][name] = report

            # Set CS/NS
            if min(read_rates) <= IO_VARS['Threshold Fail']:
                TESTS['iobenchmark']['Status'][name] = 'NS'
            elif min(read_rates) <= IO_VARS['Threshold Warn']:
                TESTS['iobenchmark']['Status'][name] = 'Unknown'
            else:
                TESTS['iobenchmark']['Status'][name] = 'CS'

            # Save logs
            dest_filename = '{}/iobenchmark-{}.log'.format(global_vars['LogDir'], name)
            shutil.move(progress_file, dest_filename)
            with open(dest_filename.replace('.', '-raw.'), 'a') as f:
                for rate in read_rates:
                    f.write('{} MB/s\n'.format(rate/(1024**2)))
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
    for t in ['Prime95', 'NVMe/SMART', 'badblocks', 'iobenchmark']:
        TESTS[t]['Enabled'] = t in tests
    TESTS['NVMe/SMART']['Quick'] = 'Quick' in tests

    # Initialize
    if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled'] or TESTS['iobenchmark']['Enabled']:
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
        if TESTS['iobenchmark']['Enabled']:
            run_iobenchmark()
    
    # Show results
    show_results()

    # Open log
    if not TESTS['NVMe/SMART']['Quick']:
        try:
            popen_program(['nohup', 'leafpad', global_vars['LogFile']], pipe=True)
        except Exception:
            print_error('ERROR: Failed to open log: {}'.format(
                global_vars['LogFile']))
            pause('Press Enter to exit...')

def scan_disks(full_paths=False, only_path=None):
    """Scan for disks eligible for hardware testing."""
    clear_screen()
    print_standard(' ')
    print_standard('Scanning disks...')

    # Get eligible disk list
    cmd = ['lsblk', '-J', '-O']
    if full_paths:
        cmd.append('-p')
    if only_path:
        cmd.append(only_path)
    result = run_program(cmd)
    json_data = json.loads(result.stdout.decode())
    devs = {}
    for d in json_data.get('blockdevices', []):
        if d['type'] == 'disk':
            if d['hotplug'] == '0':
                devs[d['name']] = {'lsblk': d}
                TESTS['NVMe/SMART']['Status'][d['name']] = 'Pending'
                TESTS['badblocks']['Status'][d['name']] = 'Pending'
                TESTS['iobenchmark']['Status'][d['name']] = 'Pending'
            else:
                # Skip WizardKit devices
                wk_label = '{}_LINUX'.format(KIT_NAME_SHORT)
                if wk_label not in [c.get('label', '') for c in d.get('children', [])]:
                    devs[d['name']] = {'lsblk': d}
                    TESTS['NVMe/SMART']['Status'][d['name']] = 'Pending'
                    TESTS['badblocks']['Status'][d['name']] = 'Pending'
                    TESTS['iobenchmark']['Status'][d['name']] = 'Pending'
    
    for dev, data in devs.items():
        # Get SMART attributes
        run_program(
            cmd = 'sudo smartctl -s on {}{}'.format(
              '' if full_paths else '/dev/',
              dev).split(),
            check = False)
        data['smartctl'] = get_smart_details(dev)
    
        # Get NVMe attributes
        if data['lsblk']['tran'] == 'nvme':
            cmd = 'sudo nvme smart-log /dev/{} -o json'.format(dev).split()
            cmd = 'sudo nvme smart-log {}{} -o json'.format(
                '' if full_paths else '/dev/',
                dev).split()
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
        if TESTS['badblocks']['Enabled'] or TESTS['iobenchmark']['Enabled']:
            show_disk_details(data)
            needs_override = False
            if not data['Quick Health OK']:
                needs_override = True
                print_warning(
                    "WARNING: Health can't be confirmed for: /dev/{}".format(dev))
            if get_smart_value(data['smartctl'], '199'):
                # SMART attribute present and it's value is non-zero
                needs_override = True
                print_warning(
                    'WARNING: SMART 199/C7 error detected on /dev/{}'.format(dev))
                print_standard('    (Have you tried swapping the drive cable?)')
            if needs_override:
                dev_name = data['lsblk']['name']
                print_standard(' ')
                if ask('Run tests on this device anyway?'):
                    TESTS['NVMe/SMART']['Status'][dev_name] = 'OVERRIDE'
                else:
                    TESTS['NVMe/SMART']['Status'][dev_name] = 'NS'
                    TESTS['badblocks']['Status'][dev_name] = 'Denied'
                    TESTS['iobenchmark']['Status'][dev_name] = 'Denied'
                print_standard(' ') # In case there's more than one "OVERRIDE" disk

    TESTS['NVMe/SMART']['Devices'] = devs
    TESTS['badblocks']['Devices'] = devs
    TESTS['iobenchmark']['Devices'] = devs
    return devs

def show_disk_details(dev, only_attributes=False):
    """Display disk details."""
    dev_name = dev['lsblk']['name']
    if not only_attributes:
      # Device description
      print_info('Device: {}{}'.format(
          '' if '/dev/' in dev['lsblk']['name'] else '/dev/',
          dev['lsblk']['name']))
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
        if only_attributes:
            print_info('SMART Attributes:', end='')
            print_warning('             Updated: {}'.format(
                time.strftime('%Y-%m-%d %H:%M %Z')))
        else:
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
        if only_attributes:
            print_info('SMART Attributes:', end='')
            print_warning('             Updated: {}'.format(
                time.strftime('%Y-%m-%d %H:%M %Z')))
        else:
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

    # NVMe/SMART / badblocks / iobenchmark
    if TESTS['NVMe/SMART']['Enabled'] or TESTS['badblocks']['Enabled'] or TESTS['iobenchmark']['Enabled']:
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
            io_status = TESTS['iobenchmark']['Status'].get(name, None)
            if (TESTS['iobenchmark']['Enabled']
                and io_status not in ['Denied', 'OVERRIDE', 'Skipped']):
                print_info('Benchmark:')
                result = TESTS['iobenchmark']['Results'].get(name, '')
                for line in result.split('\n'):
                    print_standard('  {}'.format(line))
            print_standard(' ')

    # Done
    pause('Press Enter to return to main menu... ')
    run_program('tmux kill-pane -a'.split())

def update_io_progress(percent, rate, progress_file):
    """Update I/O progress file."""
    bar_color = COLORS['CLEAR']
    rate_color = COLORS['CLEAR']
    step = get_graph_step(rate, scale=32)
    if rate < IO_VARS['Threshold Fail']:
        bar_color = COLORS['RED']
        rate_color = COLORS['YELLOW']
    elif rate < IO_VARS['Threshold Warn']:
        bar_color = COLORS['YELLOW']
        rate_color = COLORS['YELLOW']
    elif rate > IO_VARS['Threshold Great']:
        bar_color = COLORS['GREEN']
        rate_color = COLORS['GREEN']
    line = '  {p:5.1f}%  {b_color}{b:<4}  {r_color}{r:6.1f} Mb/s{c}\n'.format(
        p=percent,
        b_color=bar_color,
        b=IO_VARS['Graph Vertical'][step],
        r_color=rate_color,
        r=rate/(1024**2),
        c=COLORS['CLEAR'])
    with open(progress_file, 'a') as f:
        f.write(line)

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
    if TESTS['iobenchmark']['Enabled']:
        output.append(' ')
        output.append('{BLUE}I/O Benchmark{CLEAR}'.format(**COLORS))
        for dev, status in sorted(TESTS['iobenchmark']['Status'].items()):
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

# vim: sts=4 sw=4 ts=4
