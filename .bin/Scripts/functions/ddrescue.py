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
AUTO_NEXT_PASS_1_THRESHOLD = 90
AUTO_NEXT_PASS_2_THRESHOLD = 98
DDRESCUE_SETTINGS = {
    '--binary-prefixes': {'Enabled': True, 'Hidden': True},
    '--data-preview': {'Enabled': True, 'Hidden': True},
    '--idirect': {'Enabled': True},
    '--odirect': {'Enabled': True},
    '--max-read-rate': {'Enabled': False, 'Value': '32MiB'},
    '--min-read-rate': {'Enabled': True, 'Value': '64KiB'},
    '--reopen-on-error': {'Enabled': True},
    '--retry-passes=': {'Enabled': True, 'Value': '0'},
    '--test-mode=': {'Enabled': False, 'Value': 'test.map'},
    '--timeout=': {'Enabled': True, 'Value': '5m'},
    '-vvvv': {'Enabled': True, 'Hidden': True},
    }
RECOMMENDED_FSTYPES = ['ext3', 'ext4', 'xfs']
SIDE_PANE_WIDTH = 21
USAGE = """    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""


# Clases
class BlockPair():
    """Object to track data and methods together for source and dest."""
    def __init__(self, source, dest, mode):
        self.source_path = source.path
        self.mode = mode
        self.name = source.name
        self.pass_done = [False, False, False]
        self.rescued = 0
        self.status = ['Pending', 'Pending', 'Pending']
        self.total_size = source.size
        # Set dest paths
        if self.mode == 'clone':
            # Cloning
            self.dest_path = dest.path
            self.map_path = '{pwd}/Clone_{prefix}.map'.format(
                pwd=os.path.realpath(global_vars['Env']['PWD']),
                prefix=source.prefix)
        else:
            # Imaging
            self.dest_path = '{path}/{prefix}.dd'.format(
                path=dest.path,
                prefix=source.prefix)
            self.map_path = '{path}/{prefix}.map'.format(
                path=dest.path,
                prefix=source.prefix)
        if os.path.exists(self.map_path):
            self.load_map_data()

    def finish_pass(self, pass_num):
        """Mark pass as done and check if 100% recovered."""
        if map_data['full recovery']:
            self.pass_done = [True, True, True]
            self.rescued = self.total_size
            self.status[pass_num] = get_formatted_status(100)
            # Mark future passes as Skipped
            pass_num += 1
            while pass_num <= 2:
                self.status[pass_num] = 'Skipped'
                pass_num += 1
        else:
            self.pass_done[pass_num] = True

    def get_pass_done(self, pass_num):
        """Return pass number's done state."""
        return self.pass_done[pass_num]

    def load_map_data(self):
        """Load data from map file and set progress."""
        map_data = read_map_file(self.map_path)
        self.rescued = map_data['rescued'] * self.total_size
        if map_data['full recovery']:
            self.pass_done = [True, True, True]
            self.rescued = self.total_size
            self.status = ['Skipped', 'Skipped', 'Skipped']
        elif map_data['non-tried'] > 0:
            # Initial pass incomplete
            pass
        elif map_data['non-trimmed'] > 0:
            self.pass_done[0] = True
            self.status[0] = 'Skipped'
        elif map_data['non-scraped'] > 0:
            self.pass_done = [True, True, False]
            self.status = ['Skipped', 'Skipped', 'Pending']

    def self_check(self):
        """Self check to abort on bad dest/map combinations."""
        dest_exists = os.path.exists(self.dest_path)
        map_exists = os.path.exists(self.map_path)
        if self.mode == 'image':
            if dest_exists and not map_exists:
                raise GenericError(
                    'Detected image "{}" but not the matching map'.format(
                        self.dest_path))
            elif not dest_exists and map_exists:
                raise GenericError(
                    'Detected map "{}" but not the matching image'.format(
                        self.map_path))
        elif not dest_exists:
            raise GenericError('Destination device "{}" missing'.format(
                self.dest_path))

    def update_progress(self, pass_num):
        """Update progress using map file."""
        if os.path.exists(self.map_path):
            map_data = read_map_file(self.map_path)
            self.rescued = map_data['rescued'] * self.total_size
            self.status[pass_num] = get_formatted_status(
                label='Pass {}'.format(pass_num),
                data=(self.rescued/self.total_size)*100)


class RecoveryState():
    """Object to track BlockPair objects and overall state."""
    def __init__(self, mode):
        self.block_pairs = []
        self.current_pass = 0
        self.finished = False
        self.mode = mode.lower()
        self.rescued = 0
        self.resumed = False
        self.started = False
        self.total_size = 0
        if mode not in ('clone', 'image'):
            raise GenericError('Unsupported mode')

    def add_block_pair(self, source, dest):
        """Run safety checks and append new BlockPair to internal list."""
        if self.mode == 'clone':
            # Cloning safety checks
            if source.is_dir():
                raise GenericError('Invalid source "{}"'.format(
                    source.path))
            elif not dest.is_dev():
                raise GenericError('Invalid destination "{}"'.format(
                    dest.path))
            elif source.size > dest.size:
                raise GenericError(
                    'Destination is too small, refusing to continue.')
        else:
            # Imaging safety checks
            if not source.is_dev():
                raise GenericError('Invalid source "{}"'.format(
                    source.path))
            elif not dest.is_dir():
                raise GenericError('Invalid destination "{}"'.format(
                    dest.path))
            elif (source.size * 1.2) > dest.size:
                raise GenericError(
                    'Destination is too small, refusing to continue.')
            elif dest.fstype.lower() not in RECOMMENDED_FSTYPES:
                print_error(
                    'Destination filesystem "{}" is not recommended.'.format(
                        dest.fstype.upper()))
                print_info('Recommended types are: {}'.format(
                    ' / '.join(RECOMMENDED_FSTYPES).upper()))
                print_standard(' ')
                if not ask('Proceed anyways? (Strongly discouraged)'):
                    raise GenericAbort()
            elif not is_writable_dir(dest):
                raise GenericError(
                    'Destination is not writable, refusing to continue.')
            elif not is_writable_filesystem(dest):
                raise GenericError(
                    'Destination is mounted read-only, refusing to continue.')
        
        # Safety checks passed
        self.block_pairs.append(BlockPair(source, dest))

    def self_checks(self):
        """Run self-checks for each BlockPair object."""
        for bp in self.block_pairs:
            bp.self_check()

    def set_pass_num(self):
        """Set current pass based on all block-pair's progress."""
        self.current_pass = 0
        for pass_num in (2, 1, 0):
            # Iterate backwards through passes
            pass_done = True
            for bp in self.block_pairs:
                pass_done &= bp.get_pass_done(pass_num)
            if pass_done:
                # All block-pairs reported being done
                # Set to next pass, unless we're on the last pass (2)
                self.current_pass = min(2, pass_num + 1)
                if pass_num == 2:
                    # Also mark overall recovery as finished if on last pass
                    self.finished = True
                break

    def update_progress(self):
        """Update overall progress using block_pairs."""
        self.rescued = 0
        self.total_size = 0
        for bp in self.block_pairs:
            self.rescued += bp.rescued
            self.total_size += bp.size
        self.status_percent = get_formatted_status(
            label='Recovered:', data=(self.rescued/self.total_size)*100)
        self.status_amount = get_formatted_status(
            label='', data=human_readable_size(self.rescued))


class BaseObj():
    """Base object used by DevObj, DirObj, and ImageObj."""
    def __init__(self, path):
        self.type = 'base'
        self.path = os.path.realpath(path)
        self.set_details()

    def is_dev(self):
        return self.type == 'dev'

    def is_dir(self):
        return self.type == 'dir'

    def is_image(self):
        return self.type == 'image'

    def self_check(self):
        pass

    def set_details(self):
        self.details = {}


class DevObj(BaseObj):
    """Block device object."""
    def self_check(self):
        """Verify that self.path points to a block device."""
        if not pathlib.Path(self.path).is_block_device():
            raise GenericError('Path "{}" is not a block device.'.format(
                self.path))

    def set_details(self):
        """Set details via lsblk."""
        self.type = 'dev'
        self.details = get_device_details(self.path)
        self.name = self.details.get('name', 'UNKNOWN')
        self.model = self.details.get('model', 'UNKNOWN')
        self.model_size = self.details.get('size', 'UNKNOWN')
        self.size = get_size_in_bytes(self.details.get('size', 'UNKNOWN'))
        self.report = get_device_report(self.path)
        self.parent = self.details.get('pkname', '')
        self.label = self.details.get('label', '')
        if not self.label:
            # Force empty string in case it's set to None
            self.label = ''
        self.update_filename_prefix()

    def update_filename_prefix(self):
        """Set filename prefix based on details."""
        self.prefix = '{m_size}_{model}'.format(
            m_size=self.model_size,
            model=self.model)
        if self.parent:
            # Add child device details
            self.prefix += '_{c_num}_{c_size}{sep}{c_label}'.format(
                c_num=self.name.replace(self.parent, ''),
                c_size=self.details.get('size', 'UNKNOWN'),
                sep='_' if self.label else '',
                c_label=self.label)


class DirObj(BaseObj):
    def self_check(self):
        """Verify that self.path points to a directory."""
        if not pathlib.Path(self.path).is_dir():
            raise GenericError('Path "{}" is not a directory.'.format(
                self.path))

    def set_details(self):
        """Set details via findmnt."""
        self.type = 'dir'
        self.details = get_dir_details(self.path)
        self.fstype = self.details.get('fstype', 'UNKNOWN')
        self.name = self.path
        self.size = get_size_in_bytes(self.details.get('avail', 'UNKNOWN'))
        self.report = get_dir_report(self.path)


class ImageObj(BaseObj):
    def self_check(self):
        """Verify that self.path points to a file."""
        if not pathlib.Path(self.path).is_file():
            raise GenericError('Path "{}" is not an image file.'.format(
                self.path))

    def set_details(self):
        """Setup loopback device, set details via lsblk, then detach device."""
        self.type = 'image'
        self.loop_dev = setup_loopback_device(self.path)
        self.details = get_device_details(self.loopdev)
        self.details['model'] = 'ImageFile'
        self.name = self.path[self.path.rfind('/')+1:]
        self.prefix = '{}_ImageFile'.format(
            self.details.get('size', 'UNKNOWN'))
        self.size = get_size_in_bytes(self.details.get('size', 'UNKNOWN'))
        self.report = get_device_report(self.loop_dev)
        self.report = self.report.replace(self.loop_dev, '{Img}')
        run_program(['losetup', '--detach', loop_path], check=False)


# Functions
def build_outer_panes(source, dest):
    """Build top and side panes."""
    clear_screen()

    # Top panes
    source_pane = tmux_splitw(
        '-bdvl', '2',
        '-PF', '#D',
        'echo-and-hold "{BLUE}Source{CLEAR}\n{text}"'.format(
            text=source['Display Name'],
            **COLORS))
    tmux_splitw(
        '-t', source_pane,
        '-dhl', '{}'.format(SIDE_PANE_WIDTH),
        'echo-and-hold "{BLUE}Started{CLEAR}\n{text}"'.format(
            text=time.strftime("%Y-%m-%d %H:%M %Z"),
            **COLORS))
    tmux_splitw(
        '-t', source_pane,
        '-dhp', '50',
        'echo-and-hold "{BLUE}Destination{CLEAR}\n{text}"'.format(
            text=dest['Display Name'],
            **COLORS))

    # Side pane
    update_progress(source)
    tmux_splitw(
        '-dhl', '{}'.format(SIDE_PANE_WIDTH),
        'watch', '--color', '--no-title', '--interval', '1',
        'cat', source['Progress Out'])


def create_path_obj(path):
    """Create Dev, Dir, or Image obj based on path given."""
    obj = None
    if pathlib.Path(self.path).is_block_device():
        obj = Dev(path)
    elif pathlib.Path(self.path).is_dir():
        obj = DirObj(path)
    elif pathlib.Path(self.path).is_file():
        obj = ImageObj(path)
    else:
        raise GenericError('Invalid path "{}"'.format(path))
    return obj


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
        # Return empty dict and let calling section deal with the issue
        return {}

    json_data = json.loads(result.stdout.decode())
    # Just return the first device (there should only be one)
    return json_data['blockdevices'][0]


def get_device_report(dev_path):
    """Build colored device report using lsblk, returns str."""
    result = run_program([
        'lsblk', '--nodeps',
        '--output', 'NAME,TRAN,TYPE,SIZE,VENDOR,MODEL,SERIAL',
        dev_path])
    lines = result.stdout.decode().strip().splitlines()
    lines.append('')

    # FS details (if any)
    result = run_program([
        'lsblk',
        '--output', 'NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT',
        dev_path])
    lines.extend(result.stdout.decode().strip().splitlines())

    # Color label lines
    output = []
    for line in lines:
        if line[0:4] == 'NAME':
            output.append('{BLUE}{line}{CLEAR}'.format(line=line, **COLORS))
        else:
            output.append(line)

    # Done
    return '\n'.join(output)


def get_dir_details(dir_path):
    """Get dir details via findmnt, returns JSON dict."""
    try:
        result = run_program([
            'findmnt', '-J',
            '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS,SIZE,AVAIL,USED',
            '-T', dir_path])
        json_data = json.loads(result.stdout.decode())
    except Exception:
        raise GenericError(
            'Failed to get directory details for "{}".'.format(self.path))
    else:
        return json_data['filesystems'][0]


def get_dir_report(dir_path):
    """Build colored dir report using findmnt, returns str."""
    output = []
    width = len(dir_path)+1
    result = run_program([
        'findmnt',
        '--output', 'SIZE,AVAIL,USED,FSTYPE,OPTIONS',
        '--target', dir_path])
    for line in result.stdout.decode().strip().splitlines():
        if 'FSTYPE' in line:
            output.append('{BLUE}{path:<{width}}{line}{CLEAR}'.format(
                path=dir_path,
                width=width,
                line=line,
                **COLORS))
        else:
            output.append('{path:<{width}}{line}'.format(
                path=dir_path,
                width=width,
                line=line))

    # Done
    return '\n'.join(output)


def get_size_in_bytes(s):
    """Convert size string from lsblk string to bytes, returns int."""
    s = re.sub(r'(\d+\.?\d*)\s*([KMGTB])B?', r'\1 \2B', s, re.IGNORECASE)
    return convert_to_bytes(s)


def get_formatted_status(label, data):
    """TODO"""
    # TODO
    pass


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
    elif s in ('Skipped', 'Unknown', 'Working'):
        color = COLORS['YELLOW']
    elif p_recovered >= t_success:
        color = COLORS['GREEN']
    elif p_recovered >= t_warn:
        color = COLORS['YELLOW']
    else:
        color = COLORS['RED']
    return color


def is_writable_dir(dir_obj):
    """Check if we have read-write-execute permissions, returns bool."""
    is_ok = True
    path_st_mode = os.stat(dir_obj.path).st_mode
    is_ok == is_ok and path_st_mode & stat.S_IRUSR
    is_ok == is_ok and path_st_mode & stat.S_IWUSR
    is_ok == is_ok and path_st_mode & stat.S_IXUSR
    return is_ok


def is_writable_filesystem(dir_obj):
    """Check if filesystem is mounted read-write, returns bool."""
    return 'rw' in dir_obj.details.get('options', '')


def mark_all_passes_pending(source):
    """Mark all devs and passes as pending in preparation for retry."""
    source['Current Pass'] = 'Pass 1'
    source['Started Recovery'] = False
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
    source['Recovered Size'] = 0
    source['Started Recovery'] = False
    source['Total Size'] = 0
    source['Type'] = 'clone'
    dest = select_device(
        'destination', dest_path,
        skip_device=source['Details'], allow_image_file=False)
    dest_safety_check(source, dest)

    # Show selection details
    show_selection_details(source, dest)

    # Set status details
    set_dest_image_paths(source, dest)
    get_recovery_scope_size(source)
    check_dest_paths(source)
    resume_from_map(source)

    # Confirm
    if not ask('Proceed with clone?'):
        raise GenericAbort()
    show_safety_check()

    # Main menu
    build_outer_panes(source, dest)
    menu_main(source, dest)

    # Done
    run_program(['losetup', '-D'])
    run_program(['tmux', 'kill-window'])
    exit_script()


def menu_ddrescue(source_path, dest_path, run_mode):
    """ddrescue menu."""
    source = None
    dest = None
    if source_path:
        source = create_path_obj(source_path)
    if dest_path:
        dest = create_path_obj(dest_path)

    # Show selection menus (if necessary)
    if not source:
        source = select_device('source')
    if not dest:
        if run_mode == 'clone':
            dest = select_device('destination', skip_device=source)
        else:
            dest = select_directory()

    # Build BlockPairs
    state = RecoveryState(run_mode)
    if run_mode == 'clone':
        state.add_block_pair(source, dest)
    else:
        # TODO select dev or child dev(s)
        pass

    # Confirmations
    # TODO Show selection details
    # TODO resume?
    # TODO Proceed? (maybe merge with resume? prompt?)
    # TODO double-confirm for clones for safety

    # Main menu
    build_outer_panes(source, dest)
    # TODO Fix
    #menu_main(source, dest)
    pause('Fake Main Menu... ')

    # Done
    run_program(['tmux', 'kill-window'])
    exit_script()

def menu_image(source_path, dest_path):
    """ddrescue imaging menu."""

    # Set devices
    source = select_device('source', source_path, allow_image_file=False)
    source['Current Pass'] = 'Pass 1'
    source['Pass 1'] = {'Status': 'Pending', 'Done': False}
    source['Pass 2'] = {'Status': 'Pending', 'Done': False}
    source['Pass 3'] = {'Status': 'Pending', 'Done': False}
    source['Recovered Size'] = 0
    source['Started Recovery'] = False
    source['Total Size'] = 0
    source['Type'] = 'image'
    dest = select_dest_path(dest_path, skip_device=source['Details'])
    dest_safety_check(source, dest)

    # Select child device(s)
    source['Children'] = menu_select_children(source)
    set_dest_image_paths(source, dest)
    get_recovery_scope_size(source)
    check_dest_paths(source)
    resume_from_map(source)

    # Show selection details
    show_selection_details(source, dest)

    # Confirm
    if not ask('Proceed with imaging?'):
        raise GenericAbort()

    # Main menu
    build_outer_panes(source, dest)
    menu_main(source, dest)

    # Done
    run_program(['losetup', '-D'])
    run_program(['tmux', 'kill-window'])
    exit_script()


def menu_main(source, dest):
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
    actions = [
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
            title=title+display_pass,
            main_entries=main_options,
            action_entries=actions)

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
                if 'Auto' in opt['Base Name']:
                    auto_run = opt['Enabled']
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
            first_run = True
            while auto_run or first_run:
                first_run = False
                run_ddrescue(source, dest, settings)
                update_progress(source, end_run=True)
                if current_pass == 'Done':
                    # "Pass Done" i.e. all passes done
                    break
                if not main_options[0]['Enabled']:
                    # Auto next pass
                    break
                if source[current_pass]['Done']:
                    min_status = source[current_pass]['Min Status']
                    if (current_pass == 'Pass 1' and
                            min_status < AUTO_NEXT_PASS_1_THRESHOLD):
                        auto_run = False
                    elif (current_pass == 'Pass 2' and
                            min_status < AUTO_NEXT_PASS_2_THRESHOLD):
                        auto_run = False
                else:
                    auto_run = False
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
    for c_details in source['Details'].get('children', []):
        dev_options.append({
            'Base Name': '{:<14}({:>6} {})'.format(
                c_details['name'],
                c_details['size'],
                c_details['fstype'] if c_details['fstype'] else 'Unknown'),
            'Details': c_details,
            'Path': c_details['name'],
            'Selected': False})
    actions = [
        {'Name': 'Proceed', 'Letter': 'P'},
        {'Name': 'Quit', 'Letter': 'Q'}]

    # Skip Menu if there's no children
    if len(dev_options) == 1:
        return []

    # Show Menu
    while True:
        one_or_more_devs_selected = False
        # Update entries
        for dev in dev_options:
            if dev['Selected']:
                one_or_more_devs_selected = True
                dev['Name'] = '* {}'.format(dev['Base Name'])
            else:
                dev['Name'] = '  {}'.format(dev['Base Name'])

        selection = menu_select(
            title='Please select part(s) to image',
            main_entries=dev_options,
            action_entries=actions)

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
        elif selection == 'P' and one_or_more_devs_selected:
            break
        elif selection == 'Q':
            raise GenericAbort()

    # Check selection
    selected_children = [{
        'Details': d['Details'],
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
        raise GenericError(
            'Failed to get device details for {}'.format(dev_path))

    # Build menu
    dev_options = []
    for dev in json_data['blockdevices']:
        # Disable dev if in skip_names
        disable_dev = dev['name'] in skip_names or dev['pkname'] in skip_names

        # Append non-matching devices
        dev_options.append({
            'Name': '{name:12} {tran:5} {size:6} {model} {serial}'.format(
                name=dev['name'],
                tran=dev['tran'] if dev['tran'] else '',
                size=dev['size'] if dev['size'] else '',
                model=dev['model'] if dev['model'] else '',
                serial=dev['serial'] if dev['serial'] else ''),
            'Path': dev['name'],
            'Disabled': disable_dev})
    dev_options = sorted(dev_options, key=itemgetter('Name'))
    if not dev_options:
        raise GenericError('No devices available.')

    # Show Menu
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    selection = menu_select(
        title=title,
        main_entries=dev_options,
        action_entries=actions,
        disabled_label='SOURCE DEVICE')

    if selection.isnumeric():
        return dev_options[int(selection)-1]['Path']
    elif selection == 'Q':
        raise GenericAbort()


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
        title='Please make a selection',
        main_entries=path_options,
        action_entries=actions)

    if selection == 'Q':
        raise GenericAbort()
    elif selection.isnumeric():
        index = int(selection) - 1
        if path_options[index]['Path']:
            # Current directory
            s_path = pwd

        elif path_options[index]['Name'] == 'Local device':
            # Local device
            local_device = select_device(
                skip_device=skip_device,
                allow_image_file=False)

            # Mount device volume(s)
            report = mount_volumes(
                all_devices=False,
                device_path=local_device['Dev Path'],
                read_write=True)

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
                title='Please select a volume',
                main_entries=vol_options,
                action_entries=actions)
            if selection.isnumeric():
                s_path = vol_options[int(selection)-1]['Path']
            elif selection == 'Q':
                raise GenericAbort()

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
                    name=s['Name'],
                    **COLORS)
        selection = menu_select(
            title=title,
            main_entries=settings,
            action_entries=actions)
        if selection.isnumeric():
            index = int(selection) - 1
            flag = settings[index]['Flag']
            enabled = source['Settings'][flag]['Enabled']
            if 'Value' in source['Settings'][flag]:
                answer = choice(
                    choices=['T', 'C'],
                    prompt='Toggle or change value for "{}"'.format(flag))
                if answer == 'T':
                    # Toggle
                    source['Settings'][flag]['Enabled'] = not enabled
                else:
                    # Update value
                    source['Settings'][flag]['Value'] = get_simple_string(
                        prompt='Enter new value')
            else:
                source['Settings'][flag]['Enabled'] = not enabled
        elif selection == 'M':
            break


def read_map_file(map_path):
    """Read map file with ddrescuelog and return data as dict."""
    map_data = {}
    result = run_program(['ddrescuelog', '-t', map_path])

    # Parse output
    for line in result.stdout.decode().splitlines():
        m = re.match(
            r'^\s*(?P<key>\S+):.*\(\s*(?P<value>\d+\.?\d*)%.*', line.strip())
        if m:
            try:
                map_data[m.group('key')] = float(m.group('value'))
            except ValueError:
                raise GenericError('Failed to read map data')
        m = re.match(r'.*current status:\s+(?P<status>.*)', line.strip())
        if m:
            map_data['pass completed'] = bool(m.group('status') == 'finished')

    # Check if 100% done
    try:
        run_program(['ddrescuelog', '-D', map_path])
    except subprocess.CalledProcessError:
        map_data['full recovery'] = False
    else:
        map_data['full recovery'] = True

    return map_data


def run_ddrescue(source, dest, settings):
    """Run ddrescue pass."""
    current_pass = source['Current Pass']
    return_code = None

    if current_pass == 'Done':
        clear_screen()
        print_warning('Recovery already completed?')
        pause('Press Enter to return to main menu...')
        return

    # Set device(s) to clone/image
    source[current_pass]['Status'] = 'Working'
    source['Started Recovery'] = True
    source_devs = [source]
    if source['Children']:
        # Use only selected child devices
        source_devs = source['Children']

    # Set heights
    # NOTE: 12/33 is based on min heights for SMART/ddrescue panes (12+22+1sep)
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
    for s_dev in source_devs:
        if s_dev[current_pass]['Done']:
            # Move to next device
            continue
        source['Current Device'] = s_dev['Dev Path']
        s_dev[current_pass]['Status'] = 'Working'
        update_progress(source)

        # Set ddrescue cmd
        if source['Type'] == 'clone':
            cmd = [
                'ddrescue', *settings, '--force', s_dev['Dev Path'],
                dest['Dev Path'], s_dev['Dest Paths']['Map']]
        else:
            cmd = [
                'ddrescue', *settings, s_dev['Dev Path'],
                s_dev['Dest Paths']['image'], s_dev['Dest Paths']['Map']]
        if current_pass == 'Pass 1':
            cmd.extend(['--no-trim', '--no-scrape'])
        elif current_pass == 'Pass 2':
            # Allow trimming
            cmd.append('--no-scrape')
        elif current_pass == 'Pass 3':
            # Allow trimming and scraping
            pass

        # Start ddrescue
        try:
            clear_screen()
            print_info('Current dev: {}'.format(s_dev['Dev Path']))
            ddrescue_proc = popen_program(['./__choose_exit', *cmd])
            # ddrescue_proc = popen_program(['./__exit_ok', *cmd])
            # ddrescue_proc = popen_program(cmd)
            while True:
                try:
                    ddrescue_proc.wait(timeout=10)
                    sleep(2)
                    update_progress(source)
                    break
                except subprocess.TimeoutExpired:
                    update_progress(source)
        except KeyboardInterrupt:
            # Catch user abort
            pass

        # Was ddrescue aborted?
        return_code = ddrescue_proc.poll()
        if return_code is None or return_code is 130:
            clear_screen()
            print_warning('Aborted')
            break
        elif return_code:
            # i.e. not None and not 0
            print_error('Error(s) encountered, see message above.')
            break

    # Done
    if str(return_code) != '0':
        # Pause on errors
        pause('Press Enter to return to main menu... ')
    run_program(['tmux', 'kill-pane', '-t', smart_pane])


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
        raise GenericError('Invalid path "{}"'.format(dest['Path']))

    # Create ticket folder
    if ask('Create ticket folder?'):
        ticket_folder = get_simple_string('Please enter folder name')
        dest['Path'] = os.path.join(
            dest['Path'], ticket_folder)
        try:
            os.makedirs(dest['Path'], exist_ok=True)
        except OSError:
            raise GenericError(
                'Failed to create folder "{}"'.format(dest['Path']))

    # Set display name
    result = run_program(['tput', 'cols'])
    width = int(
        (int(result.stdout.decode().strip()) - SIDE_PANE_WIDTH) / 2) - 2
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
        raise GenericError('Invalid {} "{}"'.format(description, dev['Path']))

    # Get device details
    dev['Details'] = get_device_details(dev['Dev Path'])
    if 'Children' not in dev:
        dev['Children'] = []

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
    width = int(
        (int(result.stdout.decode().strip()) - SIDE_PANE_WIDTH) / 2) - 2
    if len(dev['Display Name']) > width:
        if dev['Is Image']:
            dev['Display Name'] = '...{}'.format(
                dev['Display Name'][-(width-3):])
        else:
            dev['Display Name'] = '{}...'.format(
                dev['Display Name'][:(width-3)])
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
        raise GenericError('Failed to setup loopback device for source.')
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
        raise GenericAbort()


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
    if source['Type'] == 'clone':
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
    pause()


def tmux_splitw(*args):
    """Run tmux split-window command and return output as str."""
    cmd = ['tmux', 'split-window', *args]
    result = run_program(cmd)
    return result.stdout.decode().strip()


def update_progress(source, end_run=False):
    """Update progress for source dev(s) and update status pane file."""
    current_pass = source['Current Pass']
    pass_complete_for_all_devs = True
    total_recovery = True
    source['Recovered Size'] = 0
    if current_pass != 'Done':
        source[current_pass]['Min Status'] = 100
    try:
        current_pass_num = int(current_pass[-1:])
        next_pass_num = current_pass_num + 1
    except ValueError:
        # Either Done or undefined?
        current_pass_num = -1
        next_pass_num = -1
    if 1 <= next_pass_num <= 3:
        next_pass = 'Pass {}'.format(next_pass_num)
    else:
        next_pass = 'Done'

    # Update children progress
    for child in source['Children']:
        if current_pass == 'Done':
            continue
        if os.path.exists(child['Dest Paths']['Map']):
            map_data = read_map_file(child['Dest Paths']['Map'])
            if child['Dev Path'] == source.get('Current Device', ''):
                # Current child device
                r_size = map_data['rescued']/100 * child['Size']
                child[current_pass]['Done'] = map_data['pass completed']
                if source['Started Recovery']:
                    child[current_pass]['Status'] = map_data['rescued']
                child['Recovered Size'] = r_size

            # All child devices
            pass_complete_for_all_devs &= child[current_pass]['Done']
            total_recovery &= map_data['full recovery']
            try:
                source['Recovered Size'] += child.get('Recovered Size', 0)
                source[current_pass]['Min Status'] = min(
                    source[current_pass]['Min Status'],
                    child[current_pass]['Status'])
            except TypeError:
                # Force 0% to disable auto-continue
                source[current_pass]['Min Status'] = 0
        else:
            # Map missing, assuming this pass hasn't run for this dev yet
            pass_complete_for_all_devs = False
            total_recovery = False

    # Update source progress
    if len(source['Children']) > 0:
        # Imaging parts, skip updating source progress
        pass
    elif os.path.exists(source['Dest Paths']['Map']):
        # Cloning/Imaging whole device
        map_data = read_map_file(source['Dest Paths']['Map'])
        if current_pass != 'Done':
            source[current_pass]['Done'] = map_data['pass completed']
            if source['Started Recovery']:
                source[current_pass]['Status'] = map_data['rescued']
            try:
                source[current_pass]['Min Status'] = min(
                    source[current_pass]['Min Status'],
                    source[current_pass]['Status'])
            except TypeError:
                # Force 0% to disable auto-continue
                source[current_pass]['Min Status'] = 0
            pass_complete_for_all_devs &= source[current_pass]['Done']
        source['Recovered Size'] = map_data['rescued']/100 * source['Size']
        total_recovery &= map_data['full recovery']
    else:
        # Cloning/Imaging whole device and map missing
        pass_complete_for_all_devs = False
        total_recovery = False

    # End of pass updates
    if end_run:
        if total_recovery:
            # Sweet!
            source['Current Pass'] = 'Done'
            source['Recovered Size'] = source['Total Size']
            for p_num in ['Pass 1', 'Pass 2', 'Pass 3']:
                if source[p_num]['Status'] == 'Pending':
                    source[p_num]['Status'] = 'Skipped'
                for child in source['Children']:
                    if child[p_num]['Status'] == 'Pending':
                        child[p_num]['Status'] = 'Skipped'
        elif pass_complete_for_all_devs:
            # Ready for next pass?
            source['Current Pass'] = next_pass
            if current_pass != 'Done':
                source[current_pass]['Done'] = True

    # Start building output lines
    if 'Progress Out' not in source:
        source['Progress Out'] = '{}/progress.out'.format(
            global_vars['LogDir'])
    output = []
    if source['Type'] == 'clone':
        output.append('   {BLUE}Cloning Status{CLEAR}'.format(**COLORS))
    else:
        output.append('   {BLUE}Imaging Status{CLEAR}'.format(**COLORS))
    output.append('─────────────────────')

    # Overall progress
    recovered_p = (source['Recovered Size'] / source['Total Size']) * 100
    recovered_s = human_readable_size(source['Recovered Size'])
    output.append('{BLUE}Overall Progress{CLEAR}'.format(**COLORS))
    output.append('Recovered:{s_color}{recovered_p:>9.2f} %{CLEAR}'.format(
        s_color=get_status_color(recovered_p),
        recovered_p=recovered_p,
        **COLORS))
    output.append('{recovered_s:>{width}}'.format(
        recovered_s=recovered_s, width=SIDE_PANE_WIDTH))
    output.append('─────────────────────')

    # Main device
    if source['Type'] == 'clone':
        output.append('{BLUE}{dev}{CLEAR}'.format(
            dev='Image File' if source['Is Image'] else source['Dev Path'],
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
                p_num=p_num,
                s_color=get_status_color(source[p_num]['Status']),
                s_display=s_display,
                **COLORS))
    else:
        # Image mode
        if source['Children']:
            # Just parts
            for child in source['Children']:
                output.append('{BLUE}{dev}{CLEAR}'.format(
                    dev=child['Dev Path'],
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
                    output.append(
                        '{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                            p_num=p_num,
                            s_color=get_status_color(child[p_num]['Status']),
                            s_display=s_display,
                            **COLORS))
                p = (child.get('Recovered Size', 0) / child['Size']) * 100
                output.append('Recovered:{s_color}{p:>9.2f} %{CLEAR}'.format(
                        s_color=get_status_color(p), p=p, **COLORS))
                output.append(' ')
        else:
            # Whole device
            output.append('{BLUE}{dev}{CLEAR} {YELLOW}(Whole){CLEAR}'.format(
                dev=source['Dev Path'],
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
                output.append(
                    '{p_num}{s_color}{s_display:>15}{CLEAR}'.format(
                        p_num=p_num,
                        s_color=get_status_color(source[p_num]['Status']),
                        s_display=s_display,
                        **COLORS))

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(source['Progress Out'], 'w') as f:
        f.writelines(output)


if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
