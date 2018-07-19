# Wizard Kit: Functions - ddrescue

import json
import pathlib
import psutil
import re
import signal
import stat
import time

from functions.common import *
from functions.data import *
from operator import itemgetter

# STATIC VARIABLES
AUTHORIZED_DEST_FSTYPES = ['ext3', 'ext4', 'xfs']
AUTO_NEXT_PASS_1_THRESHOLD = 85
AUTO_NEXT_PASS_2_THRESHOLD = 98
DDRESCUE_SETTINGS = {
    '--binary-prefixes': {'Enabled': True, 'Hidden': True},
    '--data-preview': {'Enabled': True, 'Hidden': True},
    '--idirect': {'Enabled': True},
    '--odirect': {'Enabled': True},
    '--max-read-rate': {'Enabled': False, 'Value': '128MiB'},
    '--min-read-rate': {'Enabled': True, 'Value': '64KiB'},
    '--reopen-on-error': {'Enabled': True},
    '--retry-passes=': {'Enabled': True, 'Value': '0'},
    '--timeout=': {'Enabled': True, 'Value': '5m'},
    '-vvvv': {'Enabled': True, 'Hidden': True},
    }
USAGE = """    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""

# Functions
def abort_ddrescue_tui():
    # TODO uncomment line below
    # run_program(['losetup', '-D'])
    abort()

def build_outer_panes(source, dest):
    """Build top and side panes."""
    clear_screen()
    
    # Top panes
    source_pane = tmux_splitw(
        '-bdvl', '2',
        '-PF', '#D',
        'echo-and-hold "{BLUE}Source{CLEAR}\n{text}"'.format(
            text = source['Display Name'],
            **COLORS))
    tmux_splitw(
        '-t', source_pane,
        '-dhl', '21',
        'echo-and-hold "{BLUE}Started{CLEAR}\n{text}"'.format(
            text = time.strftime("%Y-%m-%d %H:%M %Z"),
            **COLORS))
    tmux_splitw(
        '-t', source_pane,
        '-dhp', '50',
        'echo-and-hold "{BLUE}Destination{CLEAR}\n{text}"'.format(
            text = dest['Display Name'],
            **COLORS))
    
    # Side pane
    update_progress(source)
    tmux_splitw('-dhl', '21',
        'watch', '--color', '--no-title', '--interval', '1',
        'cat', source['Progress Out'])

def dest_safety_check(source, dest):
    """Verify the destination is appropriate for the source."""
    source_size = source['Details']['size']
    if dest['Is Dir']:
        cmd = ['findmnt', '-J',
            '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS,SIZE,AVAIL,USED',
            '-T', dest['Path']]
        result = run_program(cmd)
        try:
            json_data = json.loads(result.stdout.decode())
        except Exception:
            # Welp, let's abort
            print_error('Failed to verify destination usability.')
            abort_ddrescue_tui()
        else:
            dest_size = json_data['filesystems'][0]['avail']
            dest['Free Space'] = dest_size
            dest['Filesystem'] = json_data['filesystems'][0]['fstype']
            dest['Mount options'] = json_data['filesystems'][0]['options']
    else:
        dest_size = dest['Details']['size']

    # Fix strings before converting to bytes
    source_size = re.sub(
        r'(\d+\.?\d*)\s*([KMGTB])B?', r'\1 \2B', source_size.upper())
    dest_size = re.sub(
        r'(\d+\.?\d*)\s*([KMGTB])B?', r'\1 \2B', dest_size.upper())

    # Convert to bytes and compare size
    source_size = convert_to_bytes(source_size)
    dest_size = convert_to_bytes(dest_size)
    if source['Type'] == 'Image' and dest_size < (source_size * 1.2):
        # Imaging: ensure 120% of source size is available
        print_error(
            'Not enough free space on destination, refusing to continue.')
        print_standard('  Dest {d_size} < Required {s_size}'.format(
            d_size = human_readable_size(dest_size),
            s_size = human_readable_size(source_size * 1.2)))
        abort_ddrescue_tui()
    elif source['Type'] == 'Clone' and source_size > dest_size:
        # Cloning: ensure dest >= size
        print_error('Destination is too small, refusing to continue.')
        print_standard('  Dest {d_size} < Source {s_size}'.format(
            d_size = human_readable_size(dest_size),
            s_size = human_readable_size(source_size)))
        abort_ddrescue_tui()

    # Imaging specific checks
    if source['Type'] == 'Image':
        # Filesystem Type
        if dest['Filesystem'] not in AUTHORIZED_DEST_FSTYPES:
            print_error(
                'Destination filesystem "{}" is not a recommended type.'.format(
                dest['Filesystem']))
            if not ask('Proceed anyways? (Strongly discouraged)'):
                abort_ddrescue_tui()
        # Read-Write access
        dest_ok = True
        dest_st_mode = os.stat(dest['Path']).st_mode
        dest_ok = dest_ok and dest_st_mode & stat.S_IRUSR
        dest_ok = dest_ok and dest_st_mode & stat.S_IWUSR
        dest_ok = dest_ok and dest_st_mode & stat.S_IXUSR
        if not dest_ok:
            print_error('Destination is not writable, refusing to continue.')
            abort_ddrescue_tui()
        
        # Mount options check
        if 'rw' not in dest['Mount options'].split(','):
            print_error(
                'Destination is not mounted read-write, refusing to continue.')
            abort_ddrescue_tui()

def get_device_details(dev_path):
    """Get device details via lsblk, returns JSON dict."""
    try:
        cmd = (
            'lsblk',
            '--json',
            '--output-all',
            '--paths',
            dev_path)
        result = run_program(cmd)
    except CalledProcessError:
        print_error('Failed to get device details for {}'.format(dev_path))
        abort_ddrescue_tui()

    json_data = json.loads(result.stdout.decode())
    # Just return the first device (there should only be one)
    return json_data['blockdevices'][0]

def get_status_color(s, t_success=99, t_warn=90):
    """Get color based on status, returns str."""
    color = COLORS['CLEAR']
    p_recovered = -1
    try:
        p_recovered = float(s)
    except ValueError:
        # Status is either in lists below or will default to red
        pass
    
    if s in ('Pending',):
        color = COLORS['CLEAR']
    elif s in ('Working',):
        color = COLORS['YELLOW']
    elif p_recovered >= t_success:
        color = COLORS['GREEN']
    elif p_recovered >= t_warn:
        color = COLORS['YELLOW']
    else:
        color = COLORS['RED']
    return color

def mark_pass_complete(source):
    """Mark current pass complete for device, and overall if applicable."""
    current_pass = source['Current Pass']
    current_pass_num = int(current_pass[-1:])
    next_pass_num = current_pass_num + 1
    if 1 <= next_pass_num <= 3:
        next_pass = 'Pass {}'.format(next_pass_num)
    else:
        next_pass = 'Done'
    
    # Check children progress
    pass_complete_for_all_devs = True
    for child in source['Children']:
        if child['Dev Path'] == source['Current Device']:
            # This function was called for this device, mark complete
            child[current_pass]['Done'] = True
            # TODO remove test code
            from random import randint
            status = randint((current_pass_num-1)*10+85, 110) + randint(0, 99) / 100
            child[current_pass]['Status'] = status
        if not child[current_pass]['Done']:
            pass_complete_for_all_devs = False

    # Update source vars
    if pass_complete_for_all_devs:
        source['Current Pass'] = next_pass
        source[current_pass]['Done'] = True

    # TODO Remove test code
    if source['Children']:
        status = 100
        for child in source['Children']:
            try:
                status = min(status, child[current_pass]['Status'])
            except TypeError:
                # Force 0% to ensure we won't auto-continue to next pass
                status = 0
    else:
        from random import randint
        status = randint((current_pass_num-1)*10+75, 100) + randint(0, 99) / 100
    source[current_pass]['Status'] = status

def mark_pass_incomplete(source):
    """Mark current pass incomplete."""
    current_pass = source['Current Pass']
    source[current_pass]['Status'] = 'Incomplete'
    for child in source['Children']:
        if child['Dev Path'] == source['Current Device']:
            # This function was called for this device, mark incomplete
            child[current_pass]['Status'] = 'Incomplete'

def mark_all_passes_pending(source):
    """Mark all devs and passes as pending in preparation for retry."""
    source['Current Pass'] = 'Pass 1'
    for p_num in ['Pass 1', 'Pass 2', 'Pass 3']:
        source[p_num]['Status'] = 'Pending'
        source[p_num]['Done'] = False
        for child in source['Children']:
            child[p_num]['Status'] = 'Pending'
            child[p_num]['Done'] = False

def menu_clone(source_path, dest_path):
    """ddrescue cloning menu."""
    
    # Set devices
    source = select_device('source', source_path)
    source['Current Pass'] = 'Pass 1'
    source['Pass 1'] = {'Status': 'Pending', 'Done': False}
    source['Pass 2'] = {'Status': 'Pending', 'Done': False}
    source['Pass 3'] = {'Status': 'Pending', 'Done': False}
    source['Type'] = 'Clone'
    dest = select_device('destination', dest_path,
        skip_device = source['Details'], allow_image_file = False)
    dest_safety_check(source, dest)
    
    # Show selection details
    show_selection_details(source, dest)
    
    # Confirm
    if not ask('Proceed with clone?'):
        abort_ddrescue_tui()
    show_safety_check()
    
    # Main menu
    build_outer_panes(source, dest)
    menu_main(source)

    # Done
    run_program(['losetup', '-D'])
    run_program(['tmux', 'kill-window'])
    exit_script()

def menu_ddrescue(*args):
    """Main ddrescue loop/menu."""
    args = list(args)
    script_name = os.path.basename(args.pop(0))
    run_mode = ''
    source_path = None
    dest_path = None

    # Parse args
    try:
        run_mode = args.pop(0)
        source_path = args.pop(0)
        dest_path = args.pop(0)
    except IndexError:
        # We'll set the missing paths later
        pass

    # Show proper menu or exit
    if run_mode == 'clone':
        menu_clone(source_path, dest_path)
    elif run_mode == 'image':
        menu_image(source_path, dest_path)
    else:
        if not re.search(r'(^$|help|-h|\?)', run_mode, re.IGNORECASE):
            print_error('Invalid mode.')
        show_usage(script_name)
        exit_script()

def menu_image(source_path, dest_path):
    """ddrescue imaging menu."""
    
    # Set devices
    source = select_device('source', source_path, allow_image_file = False)
    source['Current Pass'] = 'Pass 1'
    source['Pass 1'] = {'Status': 'Pending', 'Done': False}
    source['Pass 2'] = {'Status': 'Pending', 'Done': False}
    source['Pass 3'] = {'Status': 'Pending', 'Done': False}
    source['Type'] = 'Image'
    dest = select_dest_path(dest_path, skip_device=source['Details'])
    dest_safety_check(source, dest)
    
    # Show selection details
    show_selection_details(source, dest)
    
    # Confirm
    if not ask('Proceed with imaging?'):
        abort_ddrescue_tui()

    # Select child device(s)
    source['Children'] = menu_select_children(source)
    
    # Main menu
    build_outer_panes(source, dest)
    menu_main(source)

    # Done
    run_program(['losetup', '-D'])
    run_program(['tmux', 'kill-window'])
    exit_script()

def menu_main(source):
    """Main menu is used to set ddrescue settings."""
    title = '{GREEN}ddrescue TUI: Main Menu{CLEAR}\n\n'.format(**COLORS)
    title += '{BLUE}Current pass: {CLEAR}'.format(**COLORS)
    if 'Settings' not in source:
        source['Settings'] = DDRESCUE_SETTINGS.copy()

    # Build menu
    main_options = [
        {'Base Name': 'Auto continue (if recovery % over threshold)',
            'Enabled': True},
        {'Base Name': 'Retry (mark non-rescued sectors "non-tried")',
            'Enabled': False},
        {'Base Name': 'Reverse direction', 'Enabled': False},
        ]
    actions  =[
        {'Name': 'Start', 'Letter': 'S'},
        {'Name': 'Change settings {YELLOW}(experts only){CLEAR}'.format(
            **COLORS),
            'Letter': 'C'},
        {'Name': 'Quit', 'Letter': 'Q', 'CRLF': True},
        ]

    # Show menu
    while True:
        current_pass = source['Current Pass']
        display_pass = '1 "Initial Read"'
        if current_pass == 'Pass 2':
            display_pass = '2 "Trimming bad areas"'
        elif current_pass == 'Pass 3':
            display_pass = '3 "Scraping bad areas"'
        elif current_pass == 'Done':
            display_pass = 'Done'
        # Update entries
        for opt in main_options:
            opt['Name'] = '{} {}'.format(
                '[✓]' if opt['Enabled'] else '[ ]',
                opt['Base Name'])
        
        selection = menu_select(
            title = title + display_pass,
            main_entries = main_options,
            action_entries = actions)

        if selection.isnumeric():
            # Toggle selection
            index = int(selection) - 1
            main_options[index]['Enabled'] = not main_options[index]['Enabled']
        elif selection == 'S':
            # Set settings for pass
            settings = []
            for k, v in source['Settings'].items():
                if not v['Enabled']:
                    continue
                if k[-1:] == '=':
                    settings.append('{}{}'.format(k, v['Value']))
                else:
                    settings.append(k)
                    if 'Value' in v:
                        settings.append(v['Value'])
            for opt in main_options:
                if 'Retry' in opt['Base Name'] and opt['Enabled']:
                    settings.extend(['--retrim', '--try-again'])
                    mark_all_passes_pending(source)
                    current_pass = 'Pass 1'
                if 'Reverse' in opt['Base Name'] and opt['Enabled']:
                    settings.append('--reverse')
                # Disable for next pass
                if 'Auto' not in opt['Base Name']:
                    opt['Enabled'] = False

            # Run ddrecue
            auto_run = True
            while auto_run:
                run_ddrescue(source, settings)
                auto_run = False
                if current_pass == 'Done':
                    # "Pass Done" i.e. all passes done
                    break
                if not main_options[0]['Enabled']:
                    # Auto next pass
                    break
                if source[current_pass]['Done']:
                    try:
                        recovered = float(source[current_pass]['Status'])
                    except ValueError:
                        # Nope
                        recovered = 'Nope'
                        pass
                    else:
                        if current_pass == 'Pass 1' and recovered > 85:
                            auto_run = True
                        elif current_pass == 'Pass 2' and recovered > 98:
                            auto_run = True
                # Update current pass for next iteration
                current_pass = source['Current Pass']
        
        elif selection == 'C':
            menu_settings(source)
        elif selection == 'Q':
            break

def menu_select_children(source):
    """Select child device(s) or whole disk, returns list."""
    dev_options = [{
        'Base Name': '{:<14}(Whole device)'.format(source['Dev Path']),
        'Path': source['Dev Path'],
        'Selected': True}]
    for child in source['Details'].get('children', []):
        dev_options.append({
            'Base Name': '{:<14}({:>6} {})'.format(
                child['name'],
                child['size'],
                child['fstype'] if child['fstype'] else 'Unknown'),
            'Path': child['name'],
            'Selected': False})
    actions = [
        {'Name': 'Proceed', 'Letter': 'P'},
        {'Name': 'Quit', 'Letter': 'Q'}]
    
    # Skip Menu if there's no children
    if len(dev_options) == 1:
        return []

    # Show Menu
    while True:
        # Update entries
        for dev in dev_options:
            dev['Name'] = '{} {}'.format(
                '*' if dev['Selected'] else ' ',
                dev['Base Name'])

        selection = menu_select(
            title = 'Please select part(s) to image',
            main_entries = dev_options,
            action_entries = actions)

        if selection.isnumeric():
            # Toggle selection
            index = int(selection) - 1
            dev_options[index]['Selected'] = not dev_options[index]['Selected']

            # Deselect whole device if child selected (this round)
            if index > 0:
                dev_options[0]['Selected'] = False

            # Deselect all children if whole device selected
            if dev_options[0]['Selected']:
                for dev in dev_options[1:]:
                    dev['Selected'] = False
        elif selection == 'P':
            break
        elif selection == 'Q':
            abort_ddrescue_tui()

    # Check selection
    selected_children = [{
        'Dev Path': d['Path'],
        'Pass 1': {'Status': 'Pending', 'Done': False},
        'Pass 2': {'Status': 'Pending', 'Done': False},
        'Pass 3': {'Status': 'Pending', 'Done': False}} for d in dev_options
        if d['Selected'] and 'Whole device' not in d['Base Name']]
    return selected_children

def menu_select_device(title='Which device?', skip_device={}):
    """Select block device via a menu, returns dev_path as str."""
    skip_names = [
        skip_device.get('name', None), skip_device.get('pkname', None)]
    skip_names = [n for n in skip_names if n]
    try:
        cmd = (
            'lsblk',
            '--json',
            '--nodeps',
            '--output-all',
            '--paths')
        result = run_program(cmd)
        json_data = json.loads(result.stdout.decode())
    except CalledProcessError:
        print_error('Failed to get device details for {}'.format(dev_path))
        abort_ddrescue_tui()

    # Build menu
    dev_options = []
    for dev in json_data['blockdevices']:
        # Skip if dev is in skip_names
        if dev['name'] in skip_names or dev['pkname'] in skip_names:
            continue

        # Append non-matching devices
        dev_options.append({
            'Name': '{name:12} {tran:5} {size:6} {model} {serial}'.format(
                name = dev['name'],
                tran = dev['tran'] if dev['tran'] else '',
                size = dev['size'] if dev['size'] else '',
                model = dev['model'] if dev['model'] else '',
                serial = dev['serial'] if dev['serial'] else ''),
            'Path': dev['name']})
    dev_options = sorted(dev_options, key=itemgetter('Name'))
    if not dev_options:
        print_error('No devices available.')
        abort_ddrescue_tui()

    # Show Menu
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    selection = menu_select(
        title = title,
        main_entries = dev_options,
        action_entries = actions)

    if selection.isnumeric():
        return dev_options[int(selection)-1]['Path']
    elif selection == 'Q':
        abort_ddrescue_tui()

def menu_select_path(skip_device={}):
    """Select path via menu, returns path as str."""
    pwd = os.path.realpath(global_vars['Env']['PWD'])
    s_path = None

    # Build Menu
    path_options = [
        {'Name': 'Current directory: {}'.format(pwd), 'Path': pwd},
        {'Name': 'Local device', 'Path': None},
        {'Name': 'Enter manually', 'Path': None}]
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]

    # Show Menu
    selection = menu_select(
        title = 'Please make a selection',
        main_entries = path_options,
        action_entries = actions)

    if selection == 'Q':
        abort_ddrescue_tui()
    elif selection.isnumeric():
        index = int(selection) - 1
        if path_options[index]['Path']:
            # Current directory
            s_path = pwd

        elif path_options[index]['Name'] == 'Local device':
            # Local device
            local_device = select_device(
                skip_device = skip_device,
                allow_image_file = False)

            # Mount device volume(s)
            report = mount_volumes(
                all_devices = False,
                device_path = local_device['Dev Path'],
                read_write = True)

            # Select volume
            vol_options = []
            for k, v in sorted(report.items()):
                disabled = v['show_data']['data'] == 'Failed to mount'
                if disabled:
                    name = '{name} (Failed to mount)'.format(**v)
                else:
                    name = '{name} (mounted on "{mount_point}")'.format(**v)
                vol_options.append({
                    'Name': name,
                    'Path': v['mount_point'],
                    'Disabled': disabled})
            selection = menu_select(
                title = 'Please select a volume',
                main_entries = vol_options,
                action_entries = actions)
            if selection.isnumeric():
                s_path = vol_options[int(selection)-1]['Path']
            elif selection == 'Q':
                abort_ddrescue_tui()

        elif path_options[index]['Name'] == 'Enter manually':
            # Manual entry
            while not s_path:
                m_path = input('Please enter path: ').strip()
                if m_path and pathlib.Path(m_path).is_dir():
                    s_path = os.path.realpath(m_path)
                elif m_path and pathlib.Path(m_path).is_file():
                    print_error('File "{}" exists'.format(m_path))
                else:
                    print_error('Invalid path "{}"'.format(m_path))
    return s_path

def menu_settings(source):
    """Change advanced ddrescue settings."""
    title = '{GREEN}ddrescue TUI: Expert Settings{CLEAR}\n\n'.format(**COLORS)
    title += '{YELLOW}These settings can cause {CLEAR}'.format(**COLORS)
    title += '{RED}MAJOR DAMAGE{CLEAR}{YELLOW} to drives{CLEAR}\n'.format(
        **COLORS)
    title += 'Please read the manual before making any changes'

    # Build menu
    settings = []
    for k, v in sorted(source['Settings'].items()):
        if not v.get('Hidden', False):
            settings.append({'Base Name': k.replace('=', ''), 'Flag': k})
    actions = [{'Name': 'Main Menu', 'Letter': 'M'}]

    # Show menu
    while True:
        for s in settings:
            s['Name'] = '{}{}{}'.format(
                s['Base Name'],
                ' = ' if 'Value' in source['Settings'][s['Flag']] else '',
                source['Settings'][s['Flag']].get('Value', ''))
            if not source['Settings'][s['Flag']]['Enabled']:
                s['Name'] = '{YELLOW}{name} (Disabled){CLEAR}'.format(
                    name = s['Name'],
                    **COLORS)
        selection = menu_select(
            title = title,
            main_entries = settings,
            action_entries = actions)
        if selection.isnumeric():
            index = int(selection) - 1
            flag = settings[index]['Flag']
            enabled = source['Settings'][flag]['Enabled']
            if 'Value' in source['Settings'][flag]:
                answer = choice(
                    choices = ['T', 'C'],
                    prompt = 'Toggle or change value for "{}"'.format(flag))
                if answer == 'T':
                    # Toggle
                    source['Settings'][flag]['Enabled'] = not enabled
                else:
                    # Update value
                    source['Settings'][flag]['Value'] = get_simple_string(
                        prompt = 'Enter new value')
            else:
                source['Settings'][flag]['Enabled'] = not enabled
        elif selection == 'M':
            break

def run_ddrescue(source, settings):
    """Run ddrescue pass."""
    current_pass = source['Current Pass']

    # Set pass options
    if current_pass == 'Pass 1':
        settings.extend(['--no-trim', '--no-scrape'])
    elif current_pass == 'Pass 2':
        # Allow trimming
        settings.append('--no-scrape')
    elif current_pass == 'Pass 3':
        # Allow trimming and scraping
        pass
    elif current_pass == 'Done':
        clear_screen()
        print_warning('Recovery already completed?')
        pause('Press Enter to return to main menu...')
        return
    else:
        raise GenericError("This shouldn't happen?")
    
    # Set device(s) to clone/image
    source[current_pass]['Status'] = 'Working'
    devs = [source]
    if source['Children']:
        # Use only selected child devices
        devs = source['Children']
    
    # Set heights
    ## NOTE: 12/33 is based on min heights for SMART/ddrescue panes (12+22+1sep)
    result = run_program(['tput', 'lines'])
    height = int(result.stdout.decode().strip())
    height_smart = int(height * (12 / 33))
    height_ddrescue = height - height_smart
    
    # Show SMART status
    smart_pane = tmux_splitw(
        '-bdvl', str(height_smart),
        '-PF', '#D',
        'watch', '--color', '--no-title', '--interval', '300',
        'ddrescue-tui-smart-display', source['Dev Path'])
    
    # Start pass for each selected device
    for dev in devs:
        if dev[current_pass]['Done']:
            # Move to next device
            continue
        source['Current Device'] = dev['Dev Path']
        dev[current_pass]['Status'] = 'Working'
        update_progress(source)
        
        # Start ddrescue
        try:
            clear_screen()
            print_info('Current dev: {}'.format(dev['Dev Path']))
            #ddrescue_proc = popen_program(['./__choose_exit', *settings])
            ddrescue_proc = popen_program(['./__exit_ok', *settings])
            ddrescue_proc.wait()
        except KeyboardInterrupt:
            # Catch user abort
            pass

        # Was ddrescue aborted?
        return_code = ddrescue_proc.poll()
        if return_code is None:
            print_warning('Aborted')
            mark_pass_incomplete(source)
            break
        elif return_code:
            # i.e. not None and not 0
            print_error('Error(s) encountered, see message above.')
            mark_pass_incomplete(source)
            break
        else:
            # Not None and not non-zero int, assuming 0
            mark_pass_complete(source)

    # TODO
    update_progress(source)
    print_info('Return: {}'.format(return_code))
    if str(return_code) != '0':
        pause()
    run_program(['tmux', 'kill-pane', '-t', smart_pane])
    return

    ##TODO
    #print_success('GO!')
    #if source['Pass 3']['Done']:
    #    # Go to results
    #    print_success('Done?')
    #elif source['Pass 2']['Done']:
    #    # In pass 3
    #    print_error('Pass 3')
    #    print_standard(str(settings))
    #    source['Pass 3']['Done'] = True
    #    source['Pass 3']['Status'] = '99.99'
    #elif source['Pass 1']['Done']:
    #    # In pass 2
    #    print_warning('Pass 2')
    #    settings.append('--no-scrape')
    #    print_standard(str(settings))
    #    source['Pass 2']['Done'] = True
    #    source['Pass 2']['Status'] = '98.1415'
    #else:
    #    # In pass 1
    #    print_info('Pass 1')
    #    settings.extend(['--no-trim', '--no-scrape'])
    #    print_standard(str(settings))
    #    status = source['Pass 1']['Status']
    #    if status == 'Pending':
    #        source['Pass 1']['Status'] = '78.6623'
    #    elif float(status) < 80:
    #        source['Pass 1']['Status'] = '86.1102'
    #    elif float(status) < 95:
    #        source['Pass 1']['Status'] = '97.77'
    #        source['Pass 1']['Done'] = True
    #update_progress(source)

def select_dest_path(provided_path=None, skip_device={}):
    dest = {'Is Dir': True, 'Is Image': False}

    # Set path
    if provided_path:
        dest['Path'] = provided_path
    else:
        dest['Path'] = menu_select_path(skip_device=skip_device)
    dest['Path'] = os.path.realpath(dest['Path'])

    # Check path
    if not pathlib.Path(dest['Path']).is_dir():
        print_error('Invalid path "{}"'.format(dest['Path']))
        abort_ddrescue_tui()

    # Create ticket folder
    if ask('Create ticket folder?'):
        ticket_folder = get_simple_string('Please enter folder name')
        dest['Path'] = os.path.join(
            dest['Path'], ticket_folder)
        try:
            os.makedirs(dest['Path'], exist_ok=True)
        except OSError:
            print_error('Failed to create folder "{}"'.format(
                dest['Path']))
            abort_ddrescue_tui()

    # Set display name
    result = run_program(['tput', 'cols'])
    width = int((int(result.stdout.decode().strip()) - 21) / 2) - 2
    if len(dest['Path']) > width:
        dest['Display Name'] = '...{}'.format(dest['Path'][-(width-3):])
    else:
        dest['Display Name'] = dest['Path']

    return dest

def select_device(description='device', provided_path=None,
    skip_device={}, allow_image_file=True):
    """Select device via provided path or menu, return dev as dict."""
    dev = {'Is Dir': False, 'Is Image': False}
    
    # Set path
    if provided_path:
        dev['Path'] = provided_path
    else:
        dev['Path'] = menu_select_device(
            title='Please select a {}'.format(description),
            skip_device=skip_device)
    dev['Path'] = os.path.realpath(dev['Path'])
    
    # Check path
    if pathlib.Path(dev['Path']).is_block_device():
        dev['Dev Path'] = dev['Path']
    elif allow_image_file and pathlib.Path(dev['Path']).is_file():
        dev['Dev Path'] = setup_loopback_device(dev['Path'])
        dev['Is Image'] = True
    else:
        print_error('Invalid {} "{}"'.format(description, dev['Path']))
        abort_ddrescue_tui()

    # Get device details
    dev['Details'] = get_device_details(dev['Dev Path'])
    if 'Children' not in dev:
        dev['Children'] = {}
    
    # Check for parent device(s)
    while dev['Details']['pkname']:
        print_warning('{} "{}" is a child device.'.format(
            description.title(), dev['Dev Path']))
        if ask('Use parent device "{}" instead?'.format(
            dev['Details']['pkname'])):
            # Update dev with parent info
            dev['Dev Path'] = dev['Details']['pkname']
            dev['Details'] = get_device_details(dev['Dev Path'])
        else:
            # Leave alone
            break

    # Set display name
    if dev['Is Image']:
        dev['Display Name'] = dev['Path']
    else:
        dev['Display Name'] = '{name} {size} {model}'.format(
            **dev['Details'])
    result = run_program(['tput', 'cols'])
    width = int((int(result.stdout.decode().strip()) - 21) / 2) - 2
    if len(dev['Display Name']) > width:
        if dev['Is Image']:
            dev['Display Name'] = '...{}'.format(dev['Display Name'][-(width-3):])
        else:
            dev['Display Name'] = '{}...'.format(dev['Display Name'][:(width-3)])
    else:
        dev['Display Name'] = dev['Display Name']

    return dev

def setup_loopback_device(source_path):
    """Setup a loopback device for source_path, returns dev_path as str."""
    cmd = (
        'losetup',
        '--find',
        '--partscan',
        '--show',
        source_path)
    try:
        out = run_program(cmd, check=True)
        dev_path = out.stdout.decode().strip()
        sleep(1)
    except CalledProcessError:
        print_error('Failed to setup loopback device for source.')
        abort_ddrescue_tui()
    else:
        return dev_path

def show_device_details(dev_path):
    """Display device details on screen."""
    cmd = (
        'lsblk', '--nodeps',
        '--output', 'NAME,TRAN,TYPE,SIZE,VENDOR,MODEL,SERIAL',
        dev_path)
    result = run_program(cmd)
    output = result.stdout.decode().splitlines()
    print_info(output.pop(0))
    for line in output:
        print_standard(line)

    # Children info
    cmd = ('lsblk', '--output', 'NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT', dev_path)
    result = run_program(cmd)
    output = result.stdout.decode().splitlines()
    print_info(output.pop(0))
    for line in output:
        print_standard(line)

def show_safety_check():
    """Display safety check message and get confirmation from user."""
    print_standard('\nSAFETY CHECK')
    print_warning('All data will be DELETED from the '
                  'destination device and partition(s) listed above.')
    print_warning('This is irreversible and will lead '
                  'to {CLEAR}{RED}DATA LOSS.'.format(**COLORS))
    if not ask('Asking again to confirm, is this correct?'):
        abort_ddrescue_tui()

def show_selection_details(source, dest):
    clear_screen()
    
    # Source
    print_success('Source device')
    if source['Is Image']:
        print_standard('Using image file: {}'.format(source['Path']))
        print_standard('                  (via loopback device: {})'.format(
            source['Dev Path']))
    show_device_details(source['Dev Path'])
    print_standard(' ')
    
    # Destination
    if source['Type'] == 'Clone':
        print_success('Destination device ', end='')
        print_error('(ALL DATA WILL BE DELETED)', timestamp=False)
        show_device_details(dest['Dev Path'])
    else:
        print_success('Destination path')
        print_standard(dest['Path'])
        print_info('{:<8}{}'.format('FREE', 'FSTYPE'))
        print_standard('{:<8}{}'.format(
            dest['Free Space'], dest['Filesystem']))
    print_standard(' ')

def show_usage(script_name):
    print_info('Usage:')
    print_standard(USAGE.format(script_name=script_name))

def tmux_splitw(*args):
    """Run tmux split-window command and return output as str."""
    cmd = ['tmux', 'split-window', *args]
    result = run_program(cmd)
    return result.stdout.decode().strip()

def update_progress(source):
    """Update progress file."""
    if 'Progress Out' not in source:
        source['Progress Out'] = '{}/progress.out'.format(global_vars['LogDir'])
    output = []
    if source['Type'] == 'Clone':
        output.append('   {BLUE}Cloning Status{CLEAR}'.format(**COLORS))
    else:
        output.append('   {BLUE}Imaging Status{CLEAR}'.format(**COLORS))
    output.append('─────────────────────')
    
    # Main device
    if source['Type'] == 'Clone':
        output.append('{BLUE}{dev}{CLEAR}'.format(
            dev = 'Image File' if source['Is Image'] else source['Dev Path'],
            **COLORS))
        for x in (1, 2, 3):
            p_num = 'Pass {}'.format(x)
            s_display = source[p_num]['Status']
            try:
                s_display = float(s_display)
            except ValueError:
                # Ignore and leave s_display alone
                pass
            else:
                s_display = '{:0.2f} %'.format(s_display)
            output.append('{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                p_num = p_num,
                s_color = get_status_color(source[p_num]['Status']),
                s_display = s_display,
                **COLORS))
    else:
        # Image mode
        if source['Children']:
            # Just parts
            for child in source['Children']:
                output.append('{BLUE}{dev}{CLEAR}'.format(
                    dev = child['Dev Path'],
                    **COLORS))
                for x in (1, 2, 3):
                    p_num = 'Pass {}'.format(x)
                    s_display = child[p_num]['Status']
                    try:
                        s_display = float(s_display)
                    except ValueError:
                        # Ignore and leave s_display alone
                        pass
                    else:
                        s_display = '{:0.2f} %'.format(s_display)
                    output.append('{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                        p_num = p_num,
                        s_color = get_status_color(child[p_num]['Status']),
                        s_display = s_display,
                        **COLORS))
                output.append(' ')
        else:
            # Whole device
            output.append('{BLUE}{dev}{CLEAR} {YELLOW}(Whole){CLEAR}'.format(
                dev = source['Dev Path'],
                **COLORS))
            for x in (1, 2, 3):
                p_num = 'Pass {}'.format(x)
                s_display = source[p_num]['Status']
                try:
                    s_display = float(s_display)
                except ValueError:
                    # Ignore and leave s_display alone
                    pass
                else:
                    s_display = '{:0.2f} %'.format(s_display)
                output.append('{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                    p_num = p_num,
                    s_color = get_status_color(source[p_num]['Status']),
                    s_display = s_display,
                    **COLORS))

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(source['Progress Out'], 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
