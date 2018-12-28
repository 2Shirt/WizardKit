# Wizard Kit: Functions - Windows Setup

from functions.data import *
from functions.disk import *


# STATIC VARIABLES
WINDOWS_VERSIONS = [
  {'Name': 'Windows 7 Home Basic',
    'Image File': 'Win7',
    'Image Name': 'Windows 7 HOMEBASIC'},
  {'Name': 'Windows 7 Home Premium',
    'Image File': 'Win7',
    'Image Name': 'Windows 7 HOMEPREMIUM'},
  {'Name': 'Windows 7 Professional',
    'Image File': 'Win7',
    'Image Name': 'Windows 7 PROFESSIONAL'},
  {'Name': 'Windows 7 Ultimate',
    'Image File': 'Win7',
    'Image Name': 'Windows 7 ULTIMATE'},

  {'Name': 'Windows 8.1',
    'Image File': 'Win8',
    'Image Name': 'Windows 8.1',
    'CRLF': True},
  {'Name': 'Windows 8.1 Pro',
    'Image File': 'Win8',
    'Image Name': 'Windows 8.1 Pro'},

  {'Name': 'Windows 10 Home',
    'Image File': 'Win10',
    'Image Name': 'Windows 10 Home',
    'CRLF': True},
  {'Name': 'Windows 10 Pro',
    'Image File': 'Win10',
    'Image Name': 'Windows 10 Pro'},
  ]


def find_windows_image(windows_version):
  """Search for a Windows source image file, returns dict.

  Searches on local disks and then the WINDOWS_SERVER share."""
  image = {}
  imagefile = windows_version['Image File']
  imagename = windows_version['Image Name']

  # Search local source
  set_thread_error_mode(silent=True) # Prevents "No disk" popups
  for d in psutil.disk_partitions():
    for ext in ['esd', 'wim', 'swm']:
      path = '{}images\{}.{}'.format(d.mountpoint, imagefile, ext)
      if os.path.isfile(path) and wim_contains_image(path, imagename):
        image['Path'] = path
        image['Letter'] = d.mountpoint[:1].upper()
        image['Local'] = True
        if ext == 'swm':
          image['Glob'] = '--ref="{}*.swm"'.format(image['Path'][:-4])
        break
  set_thread_error_mode(silent=False) # Return to normal

  # Check for network source
  if not image:
    mount_windows_share()
    if WINDOWS_SERVER['Mounted']:
      for ext in ['esd', 'wim', 'swm']:
        path = r'\\{}\{}\images\{}.{}'.format(
          WINDOWS_SERVER['IP'],
          WINDOWS_SERVER['Share'],
          imagefile,
          ext)
        if os.path.isfile(path) and wim_contains_image(path, imagename):
          image['Path'] = path
          image['Letter'] = None
          image['Local'] = False
          if ext == 'swm':
            image['Glob'] = '--ref="{}*.swm"'.format(
              image['Path'][:-4])
          break

  # Display image to be used (if any) and return
  if image:
    print_info('Using image: {}'.format(image['Path']))
    return image
  else:
    print_error('Failed to find Windows source image for {}'.format(
      windows_version['Name']))
    raise GenericAbort


def format_disk(disk, use_gpt):
  """Format disk for use as a Windows OS disk."""
  if use_gpt:
    format_gpt(disk)
  else:
    format_mbr(disk)


def format_gpt(disk):
  """Format disk for use as a Windows OS disk using the GPT layout."""
  script = [
    # Partition table
    'select disk {}'.format(disk['Number']),
    'clean',
    'convert gpt',

    # System partition
    # NOTE: ESP needs to be >= 260 for Advanced Format 4K disks
    'create partition efi size=500',
    'format quick fs=fat32 label="System"',
    'assign letter="S"',

    # Microsoft Reserved (MSR) partition
    'create partition msr size=128',

    # Windows partition
    'create partition primary',
    'format quick fs=ntfs label="Windows"',
    'assign letter="W"',

    # Recovery Tools partition
    'shrink minimum=500',
    'create partition primary',
    'format quick fs=ntfs label="Recovery Tools"',
    'assign letter="T"',
    'set id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"',
    'gpt attributes=0x8000000000000001',
    ]

  # Run
  run_diskpart(script)


def format_mbr(disk):
  """Format disk for use as a Windows OS disk using the MBR layout."""
  script = [
    # Partition table
    'select disk {}'.format(disk['Number']),
    'clean',

    # System partition
    'create partition primary size=100',
    'format fs=ntfs quick label="System Reserved"',
    'active',
    'assign letter="S"',

    # Windows partition
    'create partition primary',
    'format fs=ntfs quick label="Windows"',
    'assign letter="W"',

    # Recovery Tools partition
    'shrink minimum=500',
    'create partition primary',
    'format quick fs=ntfs label="Recovery"',
    'assign letter="T"',
    'set id=27',
    ]

  # Run
  run_diskpart(script)


def mount_windows_share():
  """Mount the Windows images share unless already mounted."""
  if not WINDOWS_SERVER['Mounted']:
    # Mounting read-write in case a backup was done in the same session
    # and the server was left mounted read-write. This avoids throwing an
    # error by trying to mount the same server with multiple credentials.
    mount_network_share(WINDOWS_SERVER, read_write=True)


def select_windows_version():
  """Select Windows version from a menu, returns dict."""
  actions = [
    {'Name': 'Main Menu', 'Letter': 'M'},
    ]

  # Menu loop
  selection = menu_select(
    title = 'Which version of Windows are we installing?',
    main_entries = WINDOWS_VERSIONS,
    action_entries = actions)

  if selection.isnumeric():
    return WINDOWS_VERSIONS[int(selection)-1]
  elif selection == 'M':
    raise GenericAbort


def setup_windows(windows_image, windows_version):
  """Apply a Windows image to W:"""
  cmd = [
    global_vars['Tools']['wimlib-imagex'],
    'apply',
    windows_image['Path'],
    windows_version['Image Name'],
    'W:\\']
  if 'Glob' in windows_image:
    cmd.extend(windows_image['Glob'])
  run_program(cmd)


def setup_windows_re(windows_version, windows_letter='W', tools_letter='T'):
  """Setup the WinRE partition."""
  win = r'{}:\Windows'.format(windows_letter)
  winre = r'{}\System32\Recovery\WinRE.wim'.format(win)
  dest = r'{}:\Recovery\WindowsRE'.format(tools_letter)

  # Copy WinRE.wim
  os.makedirs(dest, exist_ok=True)
  shutil.copy(winre, r'{}\WinRE.wim'.format(dest))

  # Set location
  cmd = [
    r'{}\System32\ReAgentc.exe'.format(win),
    '/setreimage',
    '/path', dest,
    '/target', win]
  run_program(cmd)


def update_boot_partition(system_letter='S', windows_letter='W', mode='ALL'):
  """Setup the Windows boot partition."""
  cmd = [
    r'{}\Windows\System32\bcdboot.exe'.format(
      global_vars['Env']['SYSTEMDRIVE']),
    r'{}:\Windows'.format(windows_letter),
    '/s', '{}:'.format(system_letter),
    '/f', mode]
  run_program(cmd)


def wim_contains_image(filename, imagename):
  """Check if an ESD/WIM contains the specified image, returns bool."""
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

# vim: sts=2 sw=2 ts=2
