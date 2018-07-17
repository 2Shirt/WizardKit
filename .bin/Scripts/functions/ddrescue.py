# Wizard Kit: Functions - ddrescue

import json
import pathlib
import re
import time

from functions.common import *
from operator import itemgetter

# STATIC VARIABLES
USAGE="""    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""

# Functions
def abort_ddrescue_tui():
    run_program(['losetup', '-D'])
    abort()

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

def menu_clone(source_path, dest_path):
    """ddrescue cloning menu."""
    source_is_image = False
    source_dev_path = None
    print_success('GNU ddrescue: Cloning Menu')
    
    # Set devices
    source = select_device('source', source_path)
    source['Type'] = 'Clone'
    source['Pass 1'] = 'Pending'
    source['Pass 2'] = 'Pending'
    source['Pass 3'] = 'Pending'
    dest = select_device('destination', dest_path,
        skip_device = source['Details'], allow_image_file = False)
    
    # Show selection details
    clear_screen()
    print_success('Source device')
    if source['Is Image']:
        print_standard('Using image file: {}'.format(source['Path']))
        print_standard('                  (via loopback device: {})'.format(
            source['Dev Path']))
    show_device_details(source['Dev Path'])
    print_standard(' ')
    
    print_success('Destination device ', end='')
    print_error('(ALL DATA WILL BE DELETED)', timestamp=False)
    show_device_details(dest['Dev Path'])
    print_standard(' ')

    # Confirm
    if not ask('Proceed with clone?'):
        abort_ddrescue_tui()

    # Build outer panes
    clear_screen()
    ## Top panes
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
    ## Side pane
    update_progress(source)
    tmux_splitw('-dhl', '21',
        'watch', '--color', '--no-title', '--interval', '1',
        'cat', source['Progress Out'])
    
    # Main menu
    menu_main()

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
    print_success('GNU ddrescue: Imaging Menu')

def menu_main():
    print_success('Main Menu')
    print_standard(' ')
    print_warning('#TODO')
    print_standard(' ')
    pause('Press Enter to exit...')

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

def select_device(description='device', provided_path=None,
    skip_device={}, allow_image_file=True):
    """Select device via provided path or menu, return dev as dict."""
    dev = {'Is Image': False}
    
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
        print_error('Invalid {} "{}".'.format(description, dev['Path']))
        abort_ddrescue_tui()

    # Get device details
    dev['Details'] = get_device_details(dev['Dev Path'])
    
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
        dev['Display Name'] = '{name} {size} ({image_name})'.format(
            image_name = dev['Path'][dev['Path'].rfind('/')+1:],
            **dev['Details'])
    else:
        dev['Display Name'] = '{name} {size} {model}'.format(
            **dev['Details'])

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

def show_usage(script_name):
    print_info('Usage:')
    print_standard(USAGE.format(script_name=script_name))

def tmux_splitw(*args):
    """Run tmux split-window command and return output as str."""
    cmd = ['tmux', 'split-window', *args]
    result = run_program(cmd)
    return result.stdout.decode().strip()

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
            dev = source['Dev Path'],
            **COLORS))
        for x in (1, 2, 3):
            p_num = 'Pass {}'.format(x)
            s_display = source[p_num]
            try:
                s_display = float(s_display)
            except ValueError:
                # Ignore and leave s_display alone
                pass
            else:
                s_display = '{:0.2f} %'.format(s_display)
            output.append('{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                p_num = p_num,
                s_color = get_status_color(source[p_num]),
                s_display = s_display,
                **COLORS))
    else:
        #TODO
        pass

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(source['Progress Out'], 'w') as f:
        f.writelines(output)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
