# Wizard Kit PE: Functions - Windows Setup

from functions.data import *

# STATIC VARIABLES
DISKPART_SCRIPT = r'{}\diskpart.script'.format(global_vars['Env']['TMP'])
WINDOWS_VERSIONS = [
    {'Name': 'Windows 7 Home Basic',
        'Image File': 'Win7',
        'Image Name': 'Windows 7 HOMEBASIC',
        'Family': '7'},
    {'Name': 'Windows 7 Home Premium',
        'Image File': 'Win7',
        'Image Name': 'Windows 7 HOMEPREMIUM',
        'Family': '7'},
    {'Name': 'Windows 7 Professional', 
        'Image File': 'Win7', 
        'Image Name': 'Windows 7 PROFESSIONAL', 
        'Family': '7'},
    {'Name': 'Windows 7 Ultimate', 
        'Image File': 'Win7', 
        'Image Name': 'Windows 7 ULTIMATE', 
        'Family': '7'},
    
    {'Name': 'Windows 8.1', 
        'Image File': 'Win8', 
        'Image Name': 'Windows 8.1', 
        'Family': '8',
        'CRLF': True},
    {'Name': 'Windows 8.1 Pro', 
        'Image File': 'Win8', 
        'Image Name': 'Windows 8.1 Pro', 
        'Family': '8'},
    
    {'Name': 'Windows 10 Home', 
        'Image File': 'Win10', 
        'Image Name': 'Windows 10 Home', 
        'Family': '10',
        'CRLF': True},
    {'Name': 'Windows 10 Pro', 
        'Image File': 'Win10', 
        'Image Name': 'Windows 10 Pro', 
        'Family': '10'},
    ]

def find_windows_image(windows_version):
    """Search for a Windows source image file, returns dict.

    Searches on local drives and then the WINDOWS_SERVER share."""
    image = {}
    imagefile = windows_version['Image File']
    imagename = windows_version['Image Name']

    # Search local source
    for d in psutil.disk_partitions():
        for ext in ['esd', 'wim', 'swm']:
            path = '{}images\{}.{}'.format(d.mountpoint, imagefile, ext)
            if os.path.isfile(path) and wim_contains_image(path, imagename):
                image['Path'] = path
                image['Source'] = letter
                if ext == 'swm':
                    image['Glob'] = '--ref="{}*.swm"'.format(image['Path'][:-4])
                break

    # Check for network source
    if not image:
        mount_windows_share()
        if not WINDOWS_SERVER['Mounted']:
            return None
        for ext in ['esd', 'wim', 'swm']:
            path = r'\\{}\{}\images\{}.ext'.format(
                WINDOWS_SERVER['IP'], WINDOWS_SERVER['Share'], imagefile, ext)
            if os.path.isfile(path) and wim_contains_image(path, imagename):
                image['Path'] = path
                image['Source'] = None
                if ext == 'swm':
                    image['Glob'] = '--ref="{}*.swm"'.format(image['Path'][:-4])
                break
    
    # Display image to be used (if any) and return
    if image:
        print_info('Using image: {}'.format(image['Path']))
        return image
    else:
        print_error('Failed to find Windows source image for {}'.format(
            windows_version['Name']))
        raise GeneralAbort

def format_gpt(disk=None, windows_family=None):
    """Format disk for use as a Windows OS drive using the GPT (UEFI) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')
    if windows_family is None:
        raise Exception('No Windows family provided.')

    # Format drive
    # print_info('Drive will use a GPT (UEFI) layout.')
    with open(DISKPART_SCRIPT, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')
        script.write('convert gpt\n')

        # System partition
        script.write('create partition efi size=260\n') # NOTE: Allows for Advanced Format 4K drives
        script.write('format quick fs=fat32 label="System"\n')
        script.write('assign letter="S"\n')

        # Microsoft Reserved (MSR) partition
        script.write('create partition msr size=128\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format quick fs=ntfs label="Windows"\n')
        script.write('assign letter="W"\n')

        # Recovery Tools partition (Windows 8+)
        if re.search(r'^(8|10)', windows_family):
            script.write('shrink minimum=500\n')
            script.write('create partition primary\n')
            script.write('format quick fs=ntfs label="Recovery Tools"\n')
            script.write('assign letter="T"\n')
            script.write('set id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"\n')
            script.write('gpt attributes=0x8000000000000001\n')

    # Run script
    run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
    time.sleep(2)

def format_mbr(disk=None, windows_family=None):
    """Format disk for use as a Windows OS drive using the MBR (legacy) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')
    if windows_family is None:
        raise Exception('No Windows family provided.')

    # Format drive
    # print_info('Drive will use a MBR (legacy) layout.')
    with open(DISKPART_SCRIPT, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')

        # System partition
        script.write('create partition primary size=100\n')
        script.write('format fs=ntfs quick label="System Reserved"\n')
        script.write('active\n')
        script.write('assign letter="S"\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format fs=ntfs quick label="Windows"\n')
        script.write('assign letter="W"\n')

        # Recovery Tools partition (Windows 8+)
        if re.search(r'^(8|10)', windows_family):
            script.write('shrink minimum=500\n')
            script.write('create partition primary\n')
            script.write('format quick fs=ntfs label="Recovery"\n')
            script.write('assign letter="T"\n')
            script.write('set id=27\n')

    # Run script
    run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
    time.sleep(2)

def mount_windows_share():
    """Mount the  Windows images share unless labeled as already mounted."""
    if WINDOWS_SERVER['Mounted']:
        # Blindly skip if we mounted earlier
        continue
    
    mount_network_share(WINDOWS_SERVER)

def select_windows_version():
    actions = [{'Name': 'Main Menu', 'Letter': 'M'},]

    # Menu loop
    selection = menu_select(
        title = 'Which version of Windows are we installing?',
        main_entries = WINDOWS_VERSIONS,
        action_entries = actions)

    if selection.isnumeric():
        return WINDOWS_VERSIONS[int(selection)-1]
    elif selection == 'M':
        abort_to_main_menu()

def setup_windows(windows_image, windows_version):
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'apply',
        windows_image['Path'],
        windows_version['Image Name'],
        'W:\\']
    if 'Glob' in windows_image:
        cmd.extend(windows_image['Glob'])
    run_program(cmd)

def setup_windows_re(windows_version=None, windows_letter='W', tools_letter='T'):
    # Bail early
    if windows_version is None:
        raise Exception('Windows version not specified.')
    
    _win = '{win}:\\Windows'.format(win=windows_letter)
    _winre = '{win}\\System32\\Recovery\\WinRE.wim'.format(win=_win)
    _dest = '{tools}:\\Recovery\\WindowsRE'.format(tools=tools_letter)
    
    if re.search(r'^(8|10)', windows_version['Family']):
        # Copy WinRE.wim
        os.makedirs(_dest, exist_ok=True)
        shutil.copy(_winre, '{dest}\\WinRE.wim'.format(dest=_dest))
        
        # Set location
        run_program('{win}\\System32\\reagentc /setreimage /path {dest} /target {win}'.format(dest=_dest, win=_win))
    else:
        # Only supported on Windows 8 and above
        raise SetupError

def update_boot_partition(system_letter='S', windows_letter='W', mode='ALL'):
    run_program('bcdboot {win}:\\Windows /s {sys}: /f {mode}'.format(win=windows_letter, sys=system_letter, mode=mode))

def wim_contains_image(filename, imagename):
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'info',
        filename,
        imagename]
    try:
        run_program(cmd)
    except subprocess.CalledProcessError:
        return False
    
    return True

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
