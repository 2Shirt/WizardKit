# Wizard Kit: Functions - ddrescue

import json
import pathlib
import psutil
import re
import signal
import stat
import time

from collections import OrderedDict
from functions.common import *
from functions.data import *
from functions.hw_diags import *
from functions.tmux import *
from operator import itemgetter

# STATIC VARIABLES
AUTO_PASS_1_THRESHOLD = 95
AUTO_PASS_2_THRESHOLD = 98
DDRESCUE_SETTINGS = {
    '--binary-prefixes': {'Enabled': True, 'Hidden': True},
    '--data-preview': {'Enabled': True, 'Hidden': True, 'Value': '5'},
    '--idirect': {'Enabled': True},
    '--odirect': {'Enabled': True},
    '--max-read-rate': {'Enabled': False, 'Value': '1MiB'},
    '--min-read-rate': {'Enabled': True, 'Value': '64KiB'},
    '--reopen-on-error': {'Enabled': True},
    '--retry-passes': {'Enabled': True, 'Value': '0'},
    '--test-mode': {'Enabled': False, 'Value': 'test.map'},
    '--timeout': {'Enabled': True, 'Value': '5m'},
    '-vvvv': {'Enabled': True, 'Hidden': True},
    }
RECOMMENDED_FSTYPES = ['ext3', 'ext4', 'xfs']
SIDE_PANE_WIDTH = 21
TMUX_LAYOUT = OrderedDict({
  'Source':   {'y': 2,               'Check': True},
  'Started':  {'x': SIDE_PANE_WIDTH, 'Check': True},
  'Progress': {'x': SIDE_PANE_WIDTH, 'Check': True},
})
USAGE = """    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""


# Clases
class BaseObj():
    """Base object used by DevObj, DirObj, and ImageObj."""
    def __init__(self, path):
        self.type = 'base'
        self.parent = None
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


class BlockPair():
    """Object to track data and methods together for source and dest."""
    def __init__(self, mode, source, dest):
        self.mode = mode
        self.source = source
        self.source_path = source.path
        self.dest = dest
        self.pass_done = [False, False, False]
        self.resumed = False
        self.rescued = 0
        self.rescued_percent = 0
        self.status = ['Pending', 'Pending', 'Pending']
        self.size = source.size
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
            self.resumed = True
        self.fix_status_strings()

    def fix_status_strings(self):
        """Format status strings via get_formatted_status()."""
        for pass_num in [1, 2, 3]:
            self.status[pass_num-1] = get_formatted_status(
                label='Pass {}'.format(pass_num),
                data=self.status[pass_num-1])

    def finish_pass(self, pass_num):
        """Mark pass as done and check if 100% recovered."""
        map_data = read_map_file(self.map_path)
        if map_data['full recovery']:
            self.pass_done = [True, True, True]
            self.rescued = self.size
            self.status[pass_num] = get_formatted_status(
                label='Pass {}'.format(pass_num+1),
                data=100)
            # Mark future passes as Skipped
            pass_num += 1
            while pass_num <= 2:
                self.status[pass_num] = get_formatted_status(
                    label='Pass {}'.format(pass_num+1),
                    data='Skipped')
                pass_num += 1
        else:
            self.pass_done[pass_num] = True

    def load_map_data(self):
        """Load data from map file and set progress."""
        map_data = read_map_file(self.map_path)
        self.rescued_percent = map_data['rescued']
        self.rescued = (self.rescued_percent * self.size) / 100
        if map_data['full recovery']:
            self.pass_done = [True, True, True]
            self.rescued = self.size
            self.status = ['Skipped', 'Skipped', 'Skipped']
        elif map_data['non-tried'] > 0:
            # Initial pass incomplete
            pass
        elif map_data['non-trimmed'] > 0:
            self.pass_done = [True, False, False]
            self.status = ['Skipped', 'Pending', 'Pending']
        elif map_data['non-scraped'] > 0:
            self.pass_done = [True, True, False]
            self.status = ['Skipped', 'Skipped', 'Pending']
        else:
            self.pass_done = [True, True, True]
            self.status = ['Skipped', 'Skipped', 'Skipped']

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
            self.rescued_percent = map_data.get('rescued', 0)
            self.rescued = (self.rescued_percent * self.size) / 100
            self.status[pass_num] = get_formatted_status(
                label='Pass {}'.format(pass_num+1),
                data=(self.rescued/self.size)*100)


class DevObj(BaseObj):
    """Block device object."""
    def self_check(self):
        """Verify that self.path points to a block device."""
        if not pathlib.Path(self.path).is_block_device():
            raise GenericError('Path "{}" is not a block device.'.format(
                self.path))
        if self.parent:
            print_warning('"{}" is a child device.'.format(self.path))
            if ask('Use parent device "{}" instead?'.format(self.parent)):
                self.path = os.path.realpath(self.parent)
                self.set_details()

    def set_details(self):
        """Set details via lsblk."""
        self.type = 'dev'
        self.details = get_device_details(self.path)
        self.name = '{name} {size} {model} {serial}'.format(
            name=self.details.get('name', 'UNKNOWN'),
            size=self.details.get('size', 'UNKNOWN'),
            model=self.details.get('model', 'UNKNOWN'),
            serial=self.details.get('serial', 'UNKNOWN'))
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
        self.prefix = self.prefix.strip()
        if self.parent:
            # Add child device details
            c_num = self.path.replace(self.parent, '')
            self.prefix += '_{c_prefix}{c_num}_{c_size}{sep}{c_label}'.format(
                c_prefix='p' if len(c_num) == 1 else '',
                c_num=c_num,
                c_size=self.details.get('size', 'UNKNOWN'),
                sep='_' if self.label else '',
                c_label=self.label)
        self.prefix = self.prefix.strip().replace(' ', '_')
        self.prefix = self.prefix.strip().replace('/', '_')


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
        self.name = self.path + '/'
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
        self.details = get_device_details(self.loop_dev)
        self.details['model'] = 'ImageFile'
        self.name = '{name} {size}'.format(
            name=self.path[self.path.rfind('/')+1:],
            size=self.details.get('size', 'UNKNOWN'))
        self.prefix = '{}_ImageFile'.format(
            self.details.get('size', 'UNKNOWN'))
        self.size = get_size_in_bytes(self.details.get('size', 'UNKNOWN'))
        self.report = get_device_report(self.loop_dev)
        self.report = self.report.replace(
            self.loop_dev[self.loop_dev.rfind('/')+1:], '(Img)')
        run_program(['losetup', '--detach', self.loop_dev], check=False)


class RecoveryState():
    """Object to track BlockPair objects and overall state."""
    def __init__(self, mode, source, dest):
        self.mode = mode.lower()
        self.source = source
        self.source_path = source.path
        self.dest = dest
        self.block_pairs = []
        self.current_pass = 0
        self.current_pass_str = '0: Initializing'
        self.settings = DDRESCUE_SETTINGS.copy()
        self.finished = False
        self.panes = {}
        self.progress_out = '{}/progress.out'.format(global_vars['LogDir'])
        self.rescued = 0
        self.resumed = False
        self.started = False
        self.total_size = 0
        if mode not in ('clone', 'image'):
            raise GenericError('Unsupported mode')
        self.get_smart_source()

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
                    'Not enough free space, refusing to continue.')
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
        self.block_pairs.append(BlockPair(self.mode, source, dest))

    def current_pass_done(self):
        """Checks if pass is done for all block-pairs, returns bool."""
        done = True
        for bp in self.block_pairs:
            done &= bp.pass_done[self.current_pass]
        return done

    def current_pass_min(self):
        """Gets minimum pass rescued percentage, returns float."""
        min_percent = 100
        for bp in self.block_pairs:
            min_percent = min(min_percent, bp.rescued_percent)
        return min_percent

    def get_smart_source(self):
        """Get source for SMART dispay."""
        disk_path = self.source.path
        if self.source.parent:
            disk_path = self.source.parent

        self.smart_source = DiskObj(disk_path)

    def retry_all_passes(self):
        """Mark all passes as pending for all block-pairs."""
        self.finished = False
        for bp in self.block_pairs:
            bp.pass_done = [False, False, False]
            bp.status = ['Pending', 'Pending', 'Pending']
            bp.fix_status_strings()
        self.set_pass_num()

    def self_checks(self):
        """Run self-checks and update state values."""
        cmd = ['findmnt', '--json', '--target', os.getcwd()]
        map_allowed_fstypes = RECOMMENDED_FSTYPES.copy()
        map_allowed_fstypes.extend(['cifs', 'ext2', 'vfat'])
        map_allowed_fstypes.sort()
        json_data = {}

        # Avoid saving map to non-persistent filesystem
        try:
            result = run_program(cmd)
            json_data = json.loads(result.stdout.decode())
        except Exception:
            print_error('ERROR: Failed to verify map path')
            raise GenericAbort()
        fstype = json_data.get(
            'filesystems', [{}])[0].get(
            'fstype', 'unknown')
        if fstype not in map_allowed_fstypes:
            print_error(
                "Map isn't being saved to a recommended filesystem ({})".format(
                    fstype.upper()))
            print_info('Recommended types are: {}'.format(
                ' / '.join(map_allowed_fstypes).upper()))
            print_standard(' ')
            if not ask('Proceed anyways? (Strongly discouraged)'):
                raise GenericAbort()

        # Run BlockPair self checks and get total size
        self.total_size = 0
        for bp in self.block_pairs:
            bp.self_check()
            self.resumed |= bp.resumed
            self.total_size += bp.size

    def set_pass_num(self):
        """Set current pass based on all block-pair's progress."""
        self.current_pass = 0
        for pass_num in (2, 1, 0):
            # Iterate backwards through passes
            pass_done = True
            for bp in self.block_pairs:
                pass_done &= bp.pass_done[pass_num]
            if pass_done:
                # All block-pairs reported being done
                # Set to next pass, unless we're on the last pass (2)
                self.current_pass = min(2, pass_num + 1)
                if pass_num == 2:
                    # Also mark overall recovery as finished if on last pass
                    self.finished = True
                break
        if self.finished:
            self.current_pass_str = '- "Done"'
        elif self.current_pass == 0:
            self.current_pass_str = '1 "Initial Read"'
        elif self.current_pass == 1:
            self.current_pass_str = '2 "Trimming bad areas"'
        elif self.current_pass == 2:
            self.current_pass_str = '3 "Scraping bad areas"'

    def update_progress(self):
        """Update overall progress using block_pairs."""
        self.rescued = 0
        for bp in self.block_pairs:
            self.rescued += bp.rescued
        self.rescued_percent = (self.rescued / self.total_size) * 100
        self.status_percent = get_formatted_status(
            label='Recovered:', data=self.rescued_percent)
        self.status_amount = get_formatted_status(
            label='', data=human_readable_size(self.rescued, decimals=2))


# Functions
def build_outer_panes(state):
    """Build top and side panes."""
    state.panes['Source'] = tmux_split_window(
        behind=True, vertical=True, lines=2,
        text='{BLUE}Source{CLEAR}'.format(**COLORS))
    state.panes['Started'] = tmux_split_window(
        lines=SIDE_PANE_WIDTH, target_pane=state.panes['Source'],
        text='{BLUE}Started{CLEAR}\n{s}'.format(
            s=time.strftime("%Y-%m-%d %H:%M %Z"),
            **COLORS))
    state.panes['Destination'] = tmux_split_window(
        percent=50, target_pane=state.panes['Source'],
        text='{BLUE}Destination{CLEAR}'.format(**COLORS))

    # Side pane
    update_sidepane(state)
    state.panes['Progress'] = tmux_split_window(
        lines=SIDE_PANE_WIDTH, watch=state.progress_out)


def create_path_obj(path):
    """Create Dev, Dir, or Image obj based on path given."""
    obj = None
    if pathlib.Path(path).is_block_device():
        obj = DevObj(path)
    elif pathlib.Path(path).is_dir():
        obj = DirObj(path)
    elif pathlib.Path(path).is_file():
        obj = ImageObj(path)
    else:
        raise GenericError('Invalid path "{}"'.format(path))
    return obj


def double_confirm_clone():
    """Display warning and get 2nd confirmation from user, returns bool."""
    print_standard('\nSAFETY CHECK')
    print_warning('All data will be DELETED from the '
                  'destination device and partition(s) listed above.')
    print_warning('This is irreversible and will lead '
                  'to {CLEAR}{RED}DATA LOSS.'.format(**COLORS))
    return ask('Asking again to confirm, is this correct?')


def fix_tmux_panes(state, forced=False):
    """Fix pane sizes if the winodw has been resized."""
    needs_fixed = False

    # Check layout
    for k, v in TMUX_LAYOUT.items():
        if not    v.get('Check'):
            # Not concerned with the size of this pane
            continue
        # Get target
        target = None
        if k != 'Current':
            if k not in state.panes:
                # Skip missing panes
                continue
            else:
                target = state.panes[k]

        # Check pane size
        x, y = tmux_get_pane_size(pane_id=target)
        if v.get('x', False) and v['x'] != x:
            needs_fixed = True
        if v.get('y', False) and v['y'] != y:
            needs_fixed = True

    # Bail?
    if not needs_fixed and not forced:
        return

    # Remove Destination pane (temporarily)
    tmux_kill_pane(state.panes['Destination'])

    # Update layout
    for k, v in TMUX_LAYOUT.items():
        # Get target
        target = None
        if k != 'Current':
            if k not in state.panes:
                # Skip missing panes
                continue
            else:
                target = state.panes[k]

        # Resize pane
        tmux_resize_pane(pane_id=target, **v)

    # Calc Source/Destination pane sizes
    width, height = tmux_get_pane_size()
    width = int(width / 2) - 1

    # Update Source string
    source_str = state.source.name
    if len(source_str) > width:
        source_str = '{}...'.format(source_str[:width-3])

    # Update Destination string
    dest_str = state.dest.name
    if len(dest_str) > width:
        if state.mode == 'clone':
            dest_str = '{}...'.format(dest_str[:width-3])
        else:
            dest_str = '...{}'.format(dest_str[-width+3:])

    # Rebuild Source/Destination panes
    tmux_update_pane(
        pane_id=state.panes['Source'],
        text='{BLUE}Source{CLEAR}\n{s}'.format(
            s=source_str, **COLORS))
    state.panes['Destination'] = tmux_split_window(
        percent=50, target_pane=state.panes['Source'],
        text='{BLUE}Destination{CLEAR}\n{s}'.format(
            s=dest_str, **COLORS))

    if 'SMART' in state.panes:
        # Calc SMART/ddrescue/Journal panes sizes
        ratio = [12, 22, 4]
        width, height = tmux_get_pane_size(pane_id=state.panes['Progress'])
        height -= 2
        total = sum(ratio)
        p_ratio = [int((x/total) * height) for x in ratio]
        p_ratio[1] = height - p_ratio[0] - p_ratio[2]

        # Resize SMART/Journal panes
        tmux_resize_pane(state.panes['SMART'], y=ratio[0])
        tmux_resize_pane(y=ratio[1])
        tmux_resize_pane(state.panes['Journal'], y=ratio[2])


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
    dir_path = dir_path
    output = []
    width = len(dir_path)+1
    result = run_program([
        'findmnt',
        '--output', 'SIZE,AVAIL,USED,FSTYPE,OPTIONS',
        '--target', dir_path])
    for line in result.stdout.decode().splitlines():
        if 'FSTYPE' in line:
            output.append('{BLUE}{label:<{width}}{line}{CLEAR}'.format(
                label='PATH',
                width=width,
                line=line.replace('\n',''),
                **COLORS))
        else:
            output.append('{path:<{width}}{line}'.format(
                path=dir_path,
                width=width,
                line=line.replace('\n','')))

    # Done
    return '\n'.join(output)


def get_size_in_bytes(s):
    """Convert size string from lsblk string to bytes, returns int."""
    s = re.sub(r'(\d+\.?\d*)\s*([KMGTB])B?', r'\1 \2B', s, re.IGNORECASE)
    return convert_to_bytes(s)


def get_formatted_status(label, data):
    """Build status string using provided info, returns str."""
    data_width = SIDE_PANE_WIDTH - len(label)
    try:
        data_str = '{data:>{data_width}.2f} %'.format(
        data=data,
        data_width=data_width-2)
    except ValueError:
        # Assuming non-numeric data
        data_str = '{data:>{data_width}}'.format(
        data=data,
        data_width=data_width)
    status = '{label}{s_color}{data_str}{CLEAR}'.format(
        label=label,
        s_color=get_status_color(data),
        data_str=data_str,
        **COLORS)
    return status


def get_status_color(s, t_success=99, t_warn=90):
    """Get color based on status, returns str."""
    color = COLORS['CLEAR']
    p_recovered = -1
    try:
        p_recovered = float(s)
    except ValueError:
        # Status is either in lists below or will default to red
        pass

    if s in ('Pending',) or str(s)[-2:] in (' b', 'Kb', 'Mb', 'Gb', 'Tb'):
        color = COLORS['CLEAR']
    elif s in ('Skipped', 'Unknown'):
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


def menu_ddrescue(source_path, dest_path, run_mode):
    """ddrescue menu."""
    source = None
    dest = None
    if source_path:
        source = create_path_obj(source_path)
    else:
        source = select_device('source')
    source.self_check()
    if dest_path:
        dest = create_path_obj(dest_path)
    else:
        if run_mode == 'clone':
            dest = select_device('destination', skip_device=source)
        else:
            dest = select_path(skip_device=source)
    dest.self_check()

    # Build BlockPairs
    state = RecoveryState(run_mode, source, dest)
    if run_mode == 'clone':
        state.add_block_pair(source, dest)
    else:
        for part in select_parts(source):
            state.add_block_pair(part, dest)

    # Update state
    state.self_checks()
    state.set_pass_num()
    state.update_progress()

    # Confirmations
    clear_screen()
    show_selection_details(state)
    prompt = 'Start {}?'.format(state.mode.replace('e', 'ing'))
    if state.resumed:
        print_info('Map data detected and loaded.')
        prompt = prompt.replace('Start', 'Resume')
    if not ask(prompt):
        raise GenericAbort()
    if state.mode == 'clone' and not double_confirm_clone():
        raise GenericAbort()

    # Main menu
    clear_screen()
    build_outer_panes(state)
    fix_tmux_panes(state, forced=True)
    menu_main(state)

    # Done
    run_program(['tmux', 'kill-window'])
    exit_script()

def menu_main(state):
    """Main menu is used to set ddrescue settings."""
    title = '{GREEN}ddrescue TUI: Main Menu{CLEAR}\n\n'.format(**COLORS)
    title += '{BLUE}Current pass: {CLEAR}'.format(**COLORS)

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
        # Update entries
        for opt in main_options:
            opt['Name'] = '{} {}'.format(
                '[✓]' if opt['Enabled'] else '[ ]',
                opt['Base Name'])

        selection = menu_select(
            title=title+state.current_pass_str,
            main_entries=main_options,
            action_entries=actions)

        if selection.isnumeric():
            # Toggle selection
            index = int(selection) - 1
            main_options[index]['Enabled'] = not main_options[index]['Enabled']
        elif selection == 'S':
            # Set settings for pass
            pass_settings = []
            for k, v in state.settings.items():
                if not v['Enabled']:
                    continue
                if 'Value' in v:
                    pass_settings.append('{}={}'.format(k, v['Value']))
                else:
                    pass_settings.append(k)
            for opt in main_options:
                if 'Auto' in opt['Base Name']:
                    auto_run = opt['Enabled']
                if 'Retry' in opt['Base Name'] and opt['Enabled']:
                    pass_settings.extend(['--retrim', '--try-again'])
                    state.retry_all_passes()
                if 'Reverse' in opt['Base Name'] and opt['Enabled']:
                    pass_settings.append('--reverse')
                # Disable for next pass
                if 'Auto' not in opt['Base Name']:
                    opt['Enabled'] = False

            # Run ddrescue
            state.started = False
            while auto_run or not state.started:
                state.started = True
                run_ddrescue(state, pass_settings)
                if state.current_pass_done():
                    if (state.current_pass == 0 and
                            state.current_pass_min() < AUTO_PASS_1_THRESHOLD):
                        auto_run = False
                    elif (state.current_pass == 1 and
                            state.current_pass_min() < AUTO_PASS_2_THRESHOLD):
                        auto_run = False
                else:
                    auto_run = False
                state.set_pass_num()
                if state.finished:
                    break

        elif selection == 'C':
            menu_settings(state)
        elif selection == 'Q':
            if state.rescued_percent < 100:
                print_warning('Recovery is less than 100%')
                if ask('Are you sure you want to quit?'):
                    break
            else:
                break


def menu_settings(state):
    """Change advanced ddrescue settings."""
    title = '{GREEN}ddrescue TUI: Expert Settings{CLEAR}\n\n'.format(**COLORS)
    title += '{YELLOW}These settings can cause {CLEAR}'.format(**COLORS)
    title += '{RED}MAJOR DAMAGE{CLEAR}{YELLOW} to drives{CLEAR}\n'.format(
        **COLORS)
    title += 'Please read the manual before making any changes'

    # Build menu
    settings = []
    for k, v in sorted(state.settings.items()):
        if not v.get('Hidden', False):
            settings.append({'Base Name': k, 'Flag': k})
    actions = [{'Name': 'Main Menu', 'Letter': 'M'}]

    # Show menu
    while True:
        for s in settings:
            s['Name'] = '{}{}{}'.format(
                s['Base Name'],
                ' = ' if 'Value' in state.settings[s['Flag']] else '',
                state.settings[s['Flag']].get('Value', ''))
            if not state.settings[s['Flag']]['Enabled']:
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
            enabled = state.settings[flag]['Enabled']
            if 'Value' in state.settings[flag]:
                answer = choice(
                    choices=['T', 'C'],
                    prompt='Toggle or change value for "{}"'.format(flag))
                if answer == 'T':
                    # Toggle
                    state.settings[flag]['Enabled'] = not enabled
                else:
                    # Update value
                    state.settings[flag]['Value'] = get_simple_string(
                        prompt='Enter new value')
            else:
                state.settings[flag]['Enabled'] = not enabled
        elif selection == 'M':
            break


def read_map_file(map_path):
    """Read map file with ddrescuelog and return data as dict."""
    map_data = {'full recovery': False}
    try:
        result = run_program(['ddrescuelog', '-t', map_path])
    except CalledProcessError:
        # (Grossly) assuming map_data hasn't been saved yet, return empty dict
        return map_data

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
    except CalledProcessError:
        map_data['full recovery'] = False
    else:
        map_data['full recovery'] = True

    return map_data


def run_ddrescue(state, pass_settings):
    """Run ddrescue pass."""
    return_code = None

    if state.finished:
        clear_screen()
        print_warning('Recovery already completed?')
        pause('Press Enter to return to main menu...')
        return

    # Create SMART monitor pane
    state.smart_out = '{}/smart_{}.out'.format(
        global_vars['TmpDir'], state.smart_source.name)
    with open(state.smart_out, 'w') as f:
        f.write('Initializing...')
    state.panes['SMART'] = tmux_split_window(
        behind=True, lines=12, vertical=True, watch=state.smart_out)

    # Show systemd journal output
    state.panes['Journal'] = tmux_split_window(
        lines=4, vertical=True,
        command=['sudo', 'journalctl', '-f'])

    # Fix layout
    fix_tmux_panes(state, forced=True)

    # Run pass for each block-pair
    for bp in state.block_pairs:
        if bp.pass_done[state.current_pass]:
            # Skip to next block-pair
            continue
        update_sidepane(state)

        # Set ddrescue cmd
        cmd = [
            'ddrescue', *pass_settings,
            bp.source_path, bp.dest_path, bp.map_path]
        if state.mode == 'clone':
            cmd.append('--force')
        if state.current_pass == 0:
            cmd.extend(['--no-trim', '--no-scrape'])
        elif state.current_pass == 1:
            # Allow trimming
            cmd.append('--no-scrape')
        elif state.current_pass == 2:
            # Allow trimming and scraping
            pass

        # Start ddrescue
        try:
            clear_screen()
            print_info('Current dev: {}'.format(bp.source_path))
            ddrescue_proc = popen_program(cmd)
            i = 0
            while True:
                # Update SMART display (every 30 seconds)
                i += 1
                if i % 30 == 0:
                    state.smart_source.get_smart_details()
                    with open(state.smart_out, 'w') as f:
                        report = state.smart_source.generate_attribute_report(
                                timestamp=True)
                        for line in report:
                            f.write('{}\n'.format(line))

                # Update progress
                bp.update_progress(state.current_pass)
                update_sidepane(state)

                # Fix panes
                fix_tmux_panes(state)

                # Check if ddrescue has finished
                try:
                    ddrescue_proc.wait(timeout=1)
                    sleep(2)
                    bp.update_progress(state.current_pass)
                    update_sidepane(state)
                    break
                except subprocess.TimeoutExpired:
                    # Catch to update smart/bp/sidepane
                    pass

        except KeyboardInterrupt:
            # Catch user abort
            pass

        # Update progress/sidepane again
        bp.update_progress(state.current_pass)
        update_sidepane(state)

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
        else:
            # Mark pass finished
            bp.finish_pass(state.current_pass)
            update_sidepane(state)

    # Done
    if str(return_code) != '0':
        # Pause on errors
        pause('Press Enter to return to main menu... ')

    # Cleanup
    tmux_kill_pane(state.panes['SMART'], state.panes['Journal'])


def select_parts(source_device):
    """Select partition(s) or whole device, returns list of DevObj()s."""
    selected_parts = []
    children = source_device.details.get('children', [])

    if not children:
        # No partitions detected, auto-select whole device.
        selected_parts = [source_device]
    else:
        # Build menu
        dev_options = [{
            'Base Name': '{:<14}(Whole device)'.format(source_device.path),
            'Dev': source_device,
            'Selected': True}]
        for c_details in children:
            dev_options.append({
                'Base Name': '{:<14}({:>6} {})'.format(
                    c_details['name'],
                    c_details['size'],
                    c_details['fstype'] if c_details['fstype'] else 'Unknown'),
                'Details': c_details,
                'Dev': DevObj(c_details['name']),
                'Selected': False})
        actions = [
            {'Name': 'Proceed', 'Letter': 'P'},
            {'Name': 'Quit', 'Letter': 'Q'}]

        # Show menu
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

        # Build list of selected parts
        for d in dev_options:
            if d['Selected']:
                d['Dev'].model = source_device.model
                d['Dev'].model_size = source_device.model_size
                d['Dev'].update_filename_prefix()
                selected_parts.append(d['Dev'])

    return selected_parts


def select_path(skip_device=None):
    """Optionally mount local dev and select path, returns DirObj."""
    wd = os.path.realpath(global_vars['Env']['PWD'])
    selected_path = None

    # Build menu
    path_options = [
        {'Name': 'Current directory: {}'.format(wd), 'Path': wd},
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
        if path_options[index]['Path'] == wd:
            # Current directory
            selected_path = DirObj(wd)

        elif path_options[index]['Name'] == 'Local device':
            # Local device
            local_device = select_device(
                skip_device=skip_device)
            s_path = ''

            # Mount device volume(s)
            report = mount_volumes(
                all_devices=False,
                device_path=local_device.path,
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

            # Create folder
            if ask('Create ticket folder?'):
                ticket_folder = get_simple_string('Please enter folder name')
                s_path = os.path.join(s_path, ticket_folder)
                try:
                    os.makedirs(s_path, exist_ok=True)
                except OSError:
                    raise GenericError(
                        'Failed to create folder "{}"'.format(s_path))

            # Create DirObj
            selected_path = DirObj(s_path)

        elif path_options[index]['Name'] == 'Enter manually':
            # Manual entry
            while not selected_path:
                manual_path = input('Please enter path: ').strip()
                if manual_path and pathlib.Path(manual_path).is_dir():
                    selected_path = DirObj(manual_path)
                elif manual_path and pathlib.Path(manual_path).is_file():
                    print_error('File "{}" exists'.format(manual_path))
                else:
                    print_error('Invalid path "{}"'.format(manual_path))
    return selected_path


def select_device(description='device', skip_device=None):
    """Select device via a menu, returns DevObj."""
    cmd = (
        'lsblk',
        '--json',
        '--nodeps',
        '--output-all',
        '--paths')
    result = run_program(cmd)
    json_data = json.loads(result.stdout.decode())
    skip_names = []
    if skip_device:
        skip_names.append(skip_device.path)
        if skip_device.parent:
            skip_names.append(skip_device.parent)

    # Build menu
    dev_options = []
    for dev in json_data['blockdevices']:
        # Disable dev if in skip_names
        disabled = dev['name'] in skip_names or dev['pkname'] in skip_names

        # Add to options
        dev_options.append({
            'Name': '{name:12} {tran:5} {size:6} {model} {serial}'.format(
                name=dev['name'],
                tran=dev['tran'] if dev['tran'] else '',
                size=dev['size'] if dev['size'] else '',
                model=dev['model'] if dev['model'] else '',
                serial=dev['serial'] if dev['serial'] else ''),
            'Dev': DevObj(dev['name']),
            'Disabled': disabled})
    dev_options = sorted(dev_options, key=itemgetter('Name'))
    if not dev_options:
        raise GenericError('No devices available.')

    # Show Menu
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    selection = menu_select(
        title='Please select the {} device'.format(description),
        main_entries=dev_options,
        action_entries=actions,
        disabled_label='ALREADY SELECTED')

    if selection.isnumeric():
        return dev_options[int(selection)-1]['Dev']
    elif selection == 'Q':
        raise GenericAbort()


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


def show_selection_details(state):
    """Show selection details."""
    # Source
    print_success('Source')
    print_standard(state.source.report)
    print_standard(' ')

    # Destination
    if state.mode == 'clone':
        print_success('Destination ', end='')
        print_error('(ALL DATA WILL BE DELETED)', timestamp=False)
    else:
        print_success('Destination')
    print_standard(state.dest.report)
    print_standard(' ')


def show_usage(script_name):
    print_info('Usage:')
    print_standard(USAGE.format(script_name=script_name))
    pause()


def update_sidepane(state):
    """Update progress file for side pane."""
    output = []
    state.update_progress()
    if state.mode == 'clone':
        output.append('   {BLUE}Cloning Status{CLEAR}'.format(**COLORS))
    else:
        output.append('   {BLUE}Imaging Status{CLEAR}'.format(**COLORS))
    output.append('─────────────────────')

    # Overall progress
    output.append('{BLUE}Overall Progress{CLEAR}'.format(**COLORS))
    output.append(state.status_percent)
    output.append(state.status_amount)
    output.append('─────────────────────')

    # Source(s) progress
    for bp in state.block_pairs:
        if state.source.is_image():
            output.append('{BLUE}Image File{CLEAR}'.format(**COLORS))
        else:
            output.append('{BLUE}{source}{CLEAR}'.format(
                source=bp.source_path,
                **COLORS))
        output.extend(bp.status)
        output.append(' ')

    # Add line-endings
    output = ['{}\n'.format(line) for line in output]

    with open(state.progress_out, 'w') as f:
        f.writelines(output)


if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
