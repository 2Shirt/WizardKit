"""WizardKit: Build Kit Functions (Windows)

NOTE: This script is meant to be called from within a new kit in ConEmu.
"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import re

from wk.cfg.launchers import LAUNCHERS
from wk.cfg.main import ARCHIVE_PASSWORD, KIT_NAME_FULL
from wk.cfg.music import MUSIC_MOD, MUSIC_SNES, MUSIC_SNES_BAD
from wk.cfg.sources import SOURCES
from wk.exe import popen_program, run_program, wait_for_procs
from wk.io import copy_file, delete_item, recursive_copy, rename_item
from wk.kit.tools import (
  download_file,
  extract_archive,
  find_kit_dir,
  get_tool_path,
  )
from wk.log import update_log_path
from wk.std import (
  GenericError,
  TryAndPrint,
  clear_screen,
  pause,
  print_info,
  print_success,
  set_title,
  sleep,
  )


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
BIN_DIR = find_kit_dir('.bin')
CBIN_DIR = find_kit_dir('.cbin')
INSTALLERS_DIR = BIN_DIR.parent.joinpath('Installers')
ROOT_DIR = BIN_DIR.parent
TMP_DIR = BIN_DIR.joinpath('tmp')
IN_CONEMU = 'ConEmuPID' in os.environ
LAUNCHER_TEMPLATE = BIN_DIR.joinpath('Scripts/Launcher_Template.cmd')
REGEX_SDIO_NETWORK_DRIVERS = re.compile(
  r'DP_(WLAN|LAN_(Intel|Others|Realtek-NT))',
  re.IGNORECASE,
  )
REGEX_TORRENT_INDICES = re.compile(r'^(?P<index>\d+)\|(?P<path>.*)')
SEVEN_ZIP = get_tool_path('7-Zip', '7za')
SEVEN_ZIP_FULL = get_tool_path('7-Zip', '7z') # TODO: Replace with unrar from Pypi?
WIDTH = 50


# Functions
def compress_cbin_dirs():
  """Compress CBIN_DIR items using ARCHIVE_PASSWORD."""
  current_dir = os.getcwd()
  for item in CBIN_DIR.iterdir():
    os.chdir(item)
    cmd = [
      SEVEN_ZIP,
      'a', '-t7z', '-mx=9',
      f'-p{ARCHIVE_PASSWORD}',
      '-bso0', '-bse0', '-bsp0',
      CBIN_DIR.joinpath(f'{item.name}.7z'),
      '*',
      ]
    run_program(cmd)
    os.chdir(current_dir)
    delete_item(item, force=True, ignore_errors=True)


def delete_from_temp(item_path):
  """Delete item from temp."""
  delete_item(TMP_DIR.joinpath(item_path), force=True, ignore_errors=True)


def download_to_temp(filename, source_url):
  """Download file to temp dir, returns pathlib.Path."""
  out_path = TMP_DIR.joinpath(filename)
  download_file(out_path, source_url)
  return out_path


def extract_to_bin(archive, folder):
  """Extract archive to folder under BIN_DIR."""
  out_path = BIN_DIR.joinpath(folder)
  extract_archive(archive, out_path)


def generate_launcher(section, name, options):
  """Generate launcher script."""
  dest = ROOT_DIR.joinpath(f'{section+"/" if section else ""}{name}.cmd')
  out_text = []
  to_update = {}

  # Build list of updates
  for key, value in options.items():
    if key == 'Extra Code':
      to_update['rem EXTRA_CODE'] = '\n'.join(value)
    elif key.startswith('L_'):
      to_update[f'set {key}='] = f'set {key}={value}'

  # Build launcher script
  for line in LAUNCHER_TEMPLATE.read_text(encoding='utf-8').splitlines():
    line = line.strip() # We'll let Python handle CRLF endings
    if line in to_update:
      out_text.append(to_update[line])
    else:
      out_text.append(line)

  # Write file
  dest.parent.mkdir(exist_ok=True)
  dest.write_text('\n'.join(out_text), encoding='utf-8')


# Download functions
def download_adobe_reader():
  """Download Adobe Reader."""
  out_path = INSTALLERS_DIR.joinpath('Adobe Reader DC.exe')
  download_file(out_path, SOURCES['Adobe Reader DC'])


def download_aida64():
  """Download AIDA64."""
  archive = download_to_temp('AIDA64.zip', SOURCES['AIDA64'])
  extract_to_bin(archive, 'AIDA64')
  delete_from_temp('AIDA64.zip')


def download_autoruns():
  """Download Autoruns."""
  for item in ('Autoruns32', 'Autoruns64'):
    out_path = BIN_DIR.joinpath(f'Sysinternals/{item}.exe')
    download_file(out_path, SOURCES[item])


def download_bleachbit():
  """Download BleachBit."""
  out_path = BIN_DIR.joinpath('BleachBit')
  archive = download_to_temp('BleachBit.zip', SOURCES['BleachBit'])
  extract_archive(archive, TMP_DIR)
  for item in TMP_DIR.joinpath('BleachBit-Portable').iterdir():
    try:
      rename_item(item, out_path.joinpath(item.name))
    except FileExistsError:
      # Ignore and use our defaults
      pass
  delete_from_temp('BleachBit-Portable')
  delete_from_temp('BleachBit.zip')


def download_bluescreenview():
  """Download BlueScreenView."""
  archive_32 = download_to_temp(
    'bluescreenview32.zip', SOURCES['BlueScreenView32'],
    )
  archive_64 = download_to_temp(
    'bluescreenview64.zip', SOURCES['BlueScreenView64'],
    )
  out_path = BIN_DIR.joinpath('BlueScreenView')
  extract_archive(archive_64, out_path, 'BlueScreenView.exe')
  rename_item(
    out_path.joinpath('BlueScreenView.exe'),
    out_path.joinpath('BlueScreenView64.exe'),
    )
  extract_archive(archive_32, out_path)
  delete_from_temp('bluescreenview32.zip')
  delete_from_temp('bluescreenview64.zip')


def download_erunt():
  """Download ERUNT."""
  archive = download_to_temp('erunt.zip', SOURCES['ERUNT'])
  extract_to_bin(archive, 'ERUNT')
  delete_from_temp('erunt.zip')


def download_everything():
  """Download Everything."""
  archive_32 = download_to_temp('everything32.zip', SOURCES['Everything32'])
  archive_64 = download_to_temp('everything64.zip', SOURCES['Everything64'])
  out_path = BIN_DIR.joinpath('Everything')
  extract_archive(archive_64, out_path, 'Everything.exe')
  rename_item(
    out_path.joinpath('Everything.exe'),
    out_path.joinpath('Everything64.exe'),
    )
  extract_archive(archive_32, out_path)
  delete_from_temp('everything32.zip')
  delete_from_temp('everything64.zip')


def download_fastcopy():
  """Download FastCopy."""
  installer = download_to_temp('FastCopyInstaller.exe', SOURCES['FastCopy'])
  out_path = BIN_DIR.joinpath('FastCopy')
  tmp_path = TMP_DIR.joinpath('FastCopy64')
  run_program([installer, '/NOSUBDIR', f'/DIR={out_path}', '/EXTRACT32'])
  run_program([installer, '/NOSUBDIR', f'/DIR={tmp_path}', '/EXTRACT64'])
  rename_item(
    tmp_path.joinpath('FastCopy.exe'),
    out_path.joinpath('FastCopy64.exe'),
    )
  delete_from_temp('FastCopy64')
  delete_from_temp('FastCopyInstaller.exe')


def download_furmark():
  """Download FurMark."""
  installer = download_to_temp('FurMark_Setup.exe', SOURCES['FurMark'])
  out_path = BIN_DIR.joinpath('FurMark')
  tmp_path = TMP_DIR.joinpath('FurMarkInstall')
  run_program([installer, f'/DIR={tmp_path}', '/SILENT'])
  recursive_copy(f'{tmp_path}/', f'{out_path}/')
  delete_from_temp('FurMark_Setup.exe')
  try:
    uninstaller = list(tmp_path.glob('unins*exe'))[0]
    run_program([uninstaller, '/SILENT'])
  except IndexError as _e:
    raise GenericError('Failed to remove temporary FurMark install') from _e
  delete_from_temp('FurMarkInstall')


def download_hwinfo():
  """Download HWiNFO."""
  archive = download_to_temp('HWiNFO.zip', SOURCES['HWiNFO'])
  extract_to_bin(archive, 'HWiNFO')
  delete_from_temp('HWiNFO.zip')


def download_iobit_uninstaller():
  """Download IOBit Uninstaller."""
  installer = CBIN_DIR.joinpath('IObitUninstallerPortable.exe')
  download_file(installer, SOURCES['IOBit Uninstaller'])
  popen_program([installer])
  sleep(1)
  wait_for_procs('IObitUninstallerPortable.exe')
  delete_item(installer)


def download_macs_fan_control():
  """Download Macs Fan Control."""
  out_path = INSTALLERS_DIR.joinpath('Macs Fan Control.exe')
  download_file(out_path, SOURCES['Macs Fan Control'])


def download_libreoffice():
  """Download LibreOffice."""
  for arch in 32, 64:
    out_path = INSTALLERS_DIR.joinpath(f'LibreOffice{arch}.msi')
    download_file(out_path, SOURCES[f'LibreOffice{arch}'])


def download_neutron():
  """Download Neutron."""
  archive = download_to_temp('neutron.zip', SOURCES['Neutron'])
  out_path = BIN_DIR.joinpath('Neutron')
  extract_archive(archive, out_path, '-aos', mode='e')
  delete_from_temp('neutron.zip')


def download_notepad_plus_plus():
  """Download Notepad++."""
  archive = download_to_temp('npp.7z', SOURCES['Notepad++'])
  extract_to_bin(archive, 'NotepadPlusPlus')
  out_path = BIN_DIR.joinpath('NotepadPlusPlus')
  rename_item(
    out_path.joinpath('notepad++.exe'),
    out_path.joinpath('notepadplusplus.exe'),
    )
  delete_from_temp('npp.7z')


def download_openshell():
  """Download OpenShell installer and Fluent-Metro skin."""
  for name in ('OpenShell.exe', 'Fluent-Metro.zip'):
    out_path = BIN_DIR.joinpath(f'OpenShell/{name}')
    download_file(out_path, SOURCES[name])


def download_putty():
  """Download PuTTY."""
  archive = download_to_temp('putty.zip', SOURCES['PuTTY'])
  extract_to_bin(archive, 'PuTTY')
  delete_from_temp('putty.zip')


def download_snappy_driver_installer_origin():
  """Download Snappy Driver Installer Origin."""
  archive = download_to_temp('aria2.zip', SOURCES['Aria2'])
  aria2c = TMP_DIR.joinpath('aria2/aria2c.exe')
  extract_archive(archive, aria2c.parent, mode='e')
  index_list = []
  tmp_path = TMP_DIR.joinpath('SDIO')
  out_path = BIN_DIR.joinpath('SDIO')
  torrent_file = download_to_temp('SDIO.torrent', SOURCES['SDIO Torrent'])

  # Build file selection list
  proc = run_program([aria2c, '--show-files', torrent_file])
  for line in proc.stdout.splitlines():
    match = REGEX_TORRENT_INDICES.match(line.strip())
    if not match:
      continue
    if 'drivers' not in match.group('path').lower():
      index_list.append(match.group('index'))
    elif REGEX_SDIO_NETWORK_DRIVERS.search(match.group('path')):
      index_list.append(match.group('index'))

  # Download
  cmd = [
    aria2c,
    f'--select-file={",".join(index_list)}',
    f'--dir={tmp_path}',
    '--seed-time=0',
    torrent_file,
    ]
  if IN_CONEMU:
    cmd.append('-new_console:n')
    cmd.append('-new_console:s33V')
    popen_program(cmd, cwd=aria2c.parent)
    sleep(1)
    wait_for_procs('aria2c.exe')
  else:
    run_program(cmd)

  # Move into place
  placeholder_archive = TMP_DIR.joinpath('fake.7z')
  placeholder_archive.with_name('fake').touch()
  cmd = [
    SEVEN_ZIP,
    'a', '-t7z', '-mx=9',
    '-bso0', '-bse0', '-bsp0',
    placeholder_archive,
    placeholder_archive.with_name('fake'),
    ]
  run_program(cmd)
  for item in tmp_path.joinpath('SDIO_Update').iterdir():
    name = item.name
    if name.startswith('SDIO_') and name.endswith('.exe'):
      name = f'SDIO{"64" if "64" in name else ""}.exe'
    rename_item(item, out_path.joinpath(name))

  # Create placeholder archives (except for network drivers)
  for item in out_path.joinpath('indexes/SDI').glob('*bin'):
    archive = out_path.joinpath(f'drivers/{item.stem}.7z')
    if not REGEX_SDIO_NETWORK_DRIVERS.search(archive.name):
      copy_file(placeholder_archive, archive, overwrite=True)

  # Cleanup
  delete_from_temp('SDIO')
  delete_from_temp('SDIO.torrent')
  delete_from_temp('aria2')
  delete_from_temp('aria2.zip')
  delete_from_temp('fake')
  delete_from_temp('fake.7z')


def download_testdisk():
  """Download TestDisk."""
  archive = download_to_temp('testdisk_wip.zip', SOURCES['TestDisk'])
  out_path = BIN_DIR.joinpath('TestDisk')
  tmp_path = TMP_DIR.joinpath('TestDisk')
  extract_archive(archive, tmp_path)
  rename_item(tmp_path.joinpath('testdisk-7.2-WIP'), out_path)
  delete_from_temp('testdisk_wip.zip')


def download_wiztree():
  """Download WizTree."""
  archive = download_to_temp('wiztree.zip', SOURCES['WizTree'])
  extract_to_bin(archive, 'WizTree')
  delete_from_temp('wiztree.zip')


def download_xmplay():
  """Download XMPlay."""
  archives = [
    download_to_temp('xmplay.zip', SOURCES['XMPlay']),
    download_to_temp('xmp-7z.zip', SOURCES['XMPlay 7z']),
    download_to_temp('xmp-gme.zip', SOURCES['XMPlay Game']),
    download_to_temp('xmp-rar.zip', SOURCES['XMPlay RAR']),
    download_to_temp('Innocuous.zip', SOURCES['XMPlay Innocuous']),
    ]

  # Extract XMPlay and plugins
  extract_to_bin(archives.pop(0), 'XMPlay')
  for archive in archives:
    args = [archive, BIN_DIR.joinpath('XMPlay/plugins')]
    if archive.name == 'Innocuous.zip':
      args.append(
        'Innocuous (v1.4)/Innocuous (Hue Shifted)/'
        'Innocuous (Dark Skies - Purple-80) [L1].xmpskin'
        )
    extract_archive(*args, mode='e')

  # Cleanup
  delete_from_temp('xmplay.zip')
  delete_from_temp('xmp-7z.zip')
  delete_from_temp('xmp-gme.zip')
  delete_from_temp('xmp-rar.zip')
  delete_from_temp('Innocuous.zip')

def download_xmplay_music():
  """Download XMPlay Music."""
  music_tmp = TMP_DIR.joinpath('music')
  music_tmp.mkdir(exist_ok=True)
  current_dir = os.getcwd()
  os.chdir(music_tmp)
  url_mod = 'https://api.modarchive.org/downloads.php'
  url_rsn = 'http://snesmusic.org/v2/download.php'

  # Download music
  for song_id, song_name in MUSIC_MOD:
    download_file(
      music_tmp.joinpath(f'MOD/{song_name}'),
      f'{url_mod}?moduleid={song_id}#{song_name}',
      )
  for game in MUSIC_SNES:
    download_file(
      music_tmp.joinpath(f'SNES/{game}.rsn'),
      f'{url_rsn}?spcNow={game}',
      )

  # Extract SNES archives
  for item in music_tmp.joinpath('SNES').iterdir():
    cmd = [
      SEVEN_ZIP_FULL,
      'x', item, f'-oSNES\\{item.stem}',
      '-bso0', '-bse0', '-bsp0',
      ]
    run_program(cmd)
    delete_item(item)

  # Remove 7-Zip (Full) from kit
  delete_item(SEVEN_ZIP_FULL)
  delete_item(SEVEN_ZIP_FULL.with_name('7z.dll'))

  # Remove bad songs
  for game, globs in MUSIC_SNES_BAD.items():
    for glob in globs:
      for item in music_tmp.joinpath(f'SNES/{game}').glob(glob):
        delete_item(item)

  # Compress music
  cmd = [
    SEVEN_ZIP,
    'a', '-t7z', '-mx=9',
    '-bso0', '-bse0', '-bsp0',
    BIN_DIR.joinpath('XMPlay/music.7z'),
    'MOD', 'SNES',
    ]
  run_program(cmd)
  os.chdir(current_dir)

  # Cleanup
  delete_from_temp('music')


# "Main" Function
def build_kit():
  """Build Kit."""
  update_log_path(dest_name='Build Tool', timestamp=True)
  title = f'{KIT_NAME_FULL}: Build Tool'
  clear_screen()
  set_title(title)
  print_info(title)
  print('')

  # Set up TryAndPrint
  try_print = TryAndPrint()
  try_print.width = WIDTH
  try_print.verbose = True
  for error in ('CalledProcessError', 'FileNotFoundError'):
    try_print.add_error(error)

  # Download
  try_print.run('Adobe Reader...',            download_adobe_reader)
  try_print.run('AIDA64...',                  download_aida64)
  try_print.run('Autoruns...',                download_autoruns)
  try_print.run('BleachBit...',               download_bleachbit)
  try_print.run('BlueScreenView...',          download_bluescreenview)
  try_print.run('ERUNT...',                   download_erunt)
  try_print.run('Everything...',              download_everything)
  try_print.run('FastCopy...',                download_fastcopy)
  try_print.run('FurMark...',                 download_furmark)
  try_print.run('HWiNFO...',                  download_hwinfo)
  try_print.run('IOBit Uninstaller...',       download_iobit_uninstaller)
  try_print.run('LibreOffice...',             download_libreoffice)
  try_print.run('Macs Fan Control...',        download_macs_fan_control)
  try_print.run('Neutron...',                 download_neutron)
  try_print.run('Notepad++...',               download_notepad_plus_plus)
  try_print.run('OpenShell...',               download_openshell)
  try_print.run('PuTTY...',                   download_putty)
  try_print.run('Snappy Driver Installer...', download_snappy_driver_installer_origin)
  try_print.run('TestDisk...',                download_testdisk)
  try_print.run('WizTree...',                 download_wiztree)
  try_print.run('XMPlay...',                  download_xmplay)
  try_print.run('XMPlay Music...',            download_xmplay_music)

  # Pause
  print('', flush=True)
  pause('Please review and press Enter to continue...')

  # Compress .cbin
  try_print.run('Compress cbin...',           compress_cbin_dirs)

  # Generate launcher scripts
  print_success('Generating launchers')
  for section, launchers in sorted(LAUNCHERS.items()):
    print_info(f'  {section if section else "(Root)"}')
    for name, options in sorted(launchers.items()):
      try_print.run(
        f'    {name}...', generate_launcher,
        section, name, options,
        )

  # Done
  print('')
  print('Done.')
  pause('Press Enter to exit...')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
