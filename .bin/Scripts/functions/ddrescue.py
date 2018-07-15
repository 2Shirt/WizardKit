# Wizard Kit: Functions - ddrescue

import json
import pathlib
import re

from functions.common import *
from operator import itemgetter

# STATIC VARIABLES
USAGE="""    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""

# Functions
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
        abort()

    json_data = json.loads(result.stdout.decode())
    # Just return the first device (there should only be one)
    return json_data['blockdevices'][0]

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
        abort()
    else:
        return dev_path

def menu_clone(source_path, dest_path):
    """ddrescue cloning menu."""
    source_is_image = False
    source_dev_path = None
    print_success('GNU ddrescue: Cloning Menu')

    # Select source if not preselected
    if not source_path:
        source_path = select_device('Please select a source device')

    # Check source
    source_path = os.path.realpath(source_path)
    if pathlib.Path(source_path).is_block_device():
        source_dev_path = source_path
    elif pathlib.Path(source_path).is_file():
        source_dev_path = setup_loopback_device(source_path)
        source_is_image = True
    else:
        print_error('Invalid source "{}".'.format(source_path))
        abort()
    source_details = get_device_details(source_dev_path)

    # Check source type
    if source_details['pkname']:
        print_warning('Source "{}" is a child device.'.format(source_dev_path))
        if ask('Use parent device "{}" instead?'.format(
            source_details['pkname'])):
            source_dev_path = source_details['pkname']
            source_details = get_device_details(source_dev_path)

    # Show selection details
    print_success('Source device')
    if source_is_image:
        print_standard('Using image file: {}'.format(source_path))
        print_standard('                  (via loopback device: {})'.format(
            source_dev_path))
    show_device_details(source_dev_path)
    print_standard(' ')

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
    pass

def select_device(title='Which device?'):
    """Select block device via a menu, returns dev_path as str."""
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
        abort()

    # Build menu
    dev_options = []
    for dev in json_data['blockdevices']:
        dev_options.append({
            'Name': '{name:12} {tran:5} {size:6} {model} {serial}'.format(
                name = dev['name'],
                tran = dev['tran'] if dev['tran'] else '',
                size = dev['size'] if dev['size'] else '',
                model = dev['model'] if dev['model'] else '',
                serial = dev['serial'] if dev['serial'] else ''),
            'Path': dev['name']})
    dev_options = sorted(dev_options, key=itemgetter('Name'))
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    selection = menu_select(
        title = title,
        main_entries = dev_options,
        action_entries = actions)

    if selection.isnumeric():
        return dev_options[int(selection)-1]['Path']
    elif selection == 'Q':
        abort()

def show_usage(script_name):
    print_info('Usage:')
    print_standard(USAGE.format(script_name=script_name))

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
