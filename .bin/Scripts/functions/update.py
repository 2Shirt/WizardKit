# Wizard Kit: Functions - Build / Update

import requests

from functions.common import *
from functions.data import *
from settings.launchers import *
from settings.music import *
from settings.sources import *

def compress_and_remove_item(item):
    """Compress and delete an item unless an error is encountered."""
    try:
        compress_item(item)
    except:
        raise GenericError
    else:
        remove_item(item.path)

def compress_item(item):
    """Compress an item in a 7-Zip archive using the ARCHIVE_PASSWORD."""
    # Prep
    prev_dir = os.getcwd()
    dest = '{}.7z'.format(item.path)
    wd = item.path
    include_str = '*'
    if os.path.isfile(wd):
        wd = os.path.abspath(r'{}\{}'.format(wd, os.path.pardir))
        include_str = item.name
    os.chdir(wd)
    
    # Compress
    cmd = [
        global_vars['Tools']['SevenZip'],
        'a', dest,
        '-t7z', '-mx=7', '-myx=7', '-ms=on', '-mhe', '-bso0', '-bse0',
        '-p{}'.format(ARCHIVE_PASSWORD),
        include_str,
        ]
    run_program(cmd)
    
    # Done
    os.chdir(prev_dir)

def download_generic(out_dir, out_name, source_url):
    """Downloads a file using requests."""
    ## Code based on this Q&A: https://stackoverflow.com/q/16694907
    ### Asked by: https://stackoverflow.com/users/427457/roman-podlinov
    ### Edited by: https://stackoverflow.com/users/657427/christophe-roussy
    ### Using answer: https://stackoverflow.com/a/39217788
    ### Answer from: https://stackoverflow.com/users/4323/john-zwinck
    os.makedirs(out_dir, exist_ok=True)
    out_path = '{}/{}'.format(out_dir, out_name)
    try:
        r = requests.get(source_url, stream=True)
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        r.close()
    except:
        raise GenericError('Failed to download file.')

def download_to_temp(out_name, source_url):
    """Download a file to the TmpDir."""
    download_generic(global_vars['TmpDir'], out_name, source_url)

def extract_generic(source, dest, mode='x', sz_args=[]):
    """Extract a file to a destination."""
    cmd = [
        global_vars['Tools']['SevenZip'],
        mode, source, r'-o{}'.format(dest),
        '-aoa', '-bso0', '-bse0',
        ]
    cmd.extend(sz_args)
    run_program(cmd)

def extract_temp_to_bin(source, item, mode='x', sz_args=[]):
    """Extract a file to the .bin folder."""
    source = r'{}\{}'.format(global_vars['TmpDir'], source)
    dest = r'{}\{}'.format(global_vars['BinDir'], item)
    extract_generic(source, dest, mode, sz_args)

def extract_temp_to_cbin(source, item, mode='x', sz_args=[]):
    """Extract a file to the .cbin folder."""
    source = r'{}\{}'.format(global_vars['TmpDir'], source)
    dest = r'{}\{}'.format(global_vars['CBinDir'], item)
    include_path = r'{}\_include\{}'.format(global_vars['CBinDir'], item)
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    extract_generic(source, dest, mode, sz_args)

def generate_launcher(section, name, options):
    """Generate a launcher script."""
    # Prep
    dest = r'{}\{}'.format(global_vars['BaseDir'], section)
    if section == '(Root)':
        dest = global_vars['BaseDir']
    full_path = r'{}\{}.cmd'.format(dest, name)
    template = r'{}\Scripts\Launcher_Template.cmd'.format(global_vars['BinDir'])
    
    # Format options
    f_options = {}
    for opt in options.keys():
        # Values need to be a list to support the multi-line extra code sections
        if opt == 'Extra Code':
            f_options['rem EXTRA_CODE'] = options['Extra Code']
        elif re.search(r'^L_\w+', opt, re.IGNORECASE):
            new_opt = 'set {}='.format(opt)
            f_options[new_opt] = ['set {}={}'.format(opt, options[opt])]
    
    # Read template and update using f_options
    out_text = []
    with open(template, 'r') as f:
        for line in f.readlines():
            # Strip all lines to let Python handle/correct the CRLF endings
            line = line.strip()
            if line in f_options:
                # Extend instead of append to support extra code sections
                out_text.extend(f_options[line])
            else:
                out_text.append(line)
    
    # Write file
    os.makedirs(dest, exist_ok=True)
    with open(full_path, 'w') as f:
        # f.writelines(out_text)
        f.write('\n'.join(out_text))

def remove_item(item_path):
    """Delete a file or folder."""
    if os.path.exists(item_path):
        if os.path.isdir(item_path):
            shutil.rmtree(item_path, ignore_errors=True)
        else:
            os.remove(item_path)

def remove_from_kit(item):
    """Delete a file or folder from the .bin/.cbin folders."""
    item_locations = []
    for p in [global_vars['BinDir'], global_vars['CBinDir']]:
        item_locations.append(r'{}\{}'.format(p, item))
        item_locations.append(r'{}\_Drivers\{}'.format(p, item))
    for item_path in item_locations:
        remove_item(item_path)

def remove_from_temp(item):
    """Delete a file or folder from the TmpDir folder."""
    item_path = r'{}\{}'.format(global_vars['TmpDir'], item)
    remove_item(item_path)

def resolve_dynamic_url(source_url, regex):
    """Scan source_url for a url using the regex provided; returns str."""
    # Load the download page
    try:
        download_page = requests.get(source_url)
    except Exception:
        # "Fail silently as the download_to_temp() function will catch it
        return None

    # Scan for the url using the regex provided
    url = None
    for line in download_page.content.decode().splitlines():
        if re.search(regex, line):
            url = line.strip()
            url = re.sub(r'.*(a |)href="([^"]+)".*', r'\2', url)
            url = re.sub(r".*(a |)href='([^']+)'.*", r'\2', url)
            break

    # Return
    return url

def scan_for_net_installers(server, family_name, min_year):
    """Scan network shares for installers."""
    if not server['Mounted']:
        mount_network_share(server)
    
    if server['Mounted']:
        for year in os.scandir(r'\\{IP}\{Share}'.format(**server)):
            try:
                year_ok = int(year.name) < min_year
            except ValueError:
                year_ok = False # Skip non-year items
            if year_ok:
                # Don't support outdated installers
                continue
            for version in os.scandir(year.path):
                section = r'Installers\Extras\{}\{}'.format(
                    family_name, year.name)
                if section not in LAUNCHERS:
                    LAUNCHERS[section] = {}
                name = version.name
                if re.search(r'(exe|msi)$', name, re.IGNORECASE):
                    name = name[:-4]
                if name not in LAUNCHERS[section]:
                    LAUNCHERS[section][name] = {
                        'L_TYPE': family_name,
                        'L_PATH': year.name,
                        'L_ITEM': version.name,
                        }
        umount_network_share(server)

## Data Recovery ##
def update_testdisk():
    # Stop running processes
    for exe in ['fidentify_win.exe', 'photorec_win.exe',
        'qphotorec_win.exe', 'testdisk_win.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('TestDisk')
    
    # Download
    download_to_temp('testdisk_wip.zip', SOURCE_URLS['TestDisk'])
    
    # Extract files
    extract_temp_to_cbin('testdisk_wip.zip', 'TestDisk')
    dest = r'{}\TestDisk'.format(global_vars['CBinDir'])
    for item in os.scandir(r'{}\testdisk-7.1-WIP'.format(dest)):
        dest_item = '{}\{}'.format(dest, item.name)
        if not os.path.exists(dest_item):
            shutil.move(item.path, dest_item)
    shutil.rmtree(
        r'{}\TestDisk\testdisk-7.1-WIP'.format(global_vars['CBinDir']))
    
    # Cleanup
    remove_from_temp('testdisk_wip.zip')

## Data Transfers ##
def update_fastcopy():
    ## NOTE: Lives in .bin uncompressed
    # Stop running processes
    for process in ['FastCopy.exe', 'FastCopy64.exe']:
        kill_process(process)
    
    # Remove existing folders
    remove_from_kit('FastCopy')
    
    # Download
    download_to_temp('FastCopy.zip', SOURCE_URLS['FastCopy'])

    # Extract installer
    extract_temp_to_bin('FastCopy.zip', 'FastCopy')
    _path = r'{}\FastCopy'.format(global_vars['BinDir'])
    _installer = 'FastCopy354_installer.exe'

    # Extract 64-bit
    cmd = [
        r'{}\{}'.format(_path, _installer),
        '/NOSUBDIR', '/DIR={}'.format(_path),
        '/EXTRACT64']
    run_program(cmd)
    shutil.move(
        r'{}\FastCopy\FastCopy.exe'.format(global_vars['BinDir']),
        r'{}\FastCopy\FastCopy64.exe'.format(global_vars['BinDir']))

    # Extract 32-bit
    cmd = [
        r'{}\{}'.format(_path, _installer),
        '/NOSUBDIR', '/DIR={}'.format(_path),
        '/EXTRACT32']
    run_program(cmd)

    # Cleanup
    os.remove(r'{}\{}'.format(_path, _installer))
    os.remove(r'{}\setup.exe'.format(_path, _installer))
    remove_from_temp('FastCopy.zip')

def update_wimlib():
    # Stop running processes
    kill_process('wimlib-imagex.exe')
    
    # Remove existing folders
    remove_from_kit('wimlib')
    
    # Download
    download_to_temp('wimlib32.zip', SOURCE_URLS['wimlib32'])
    download_to_temp('wimlib64.zip', SOURCE_URLS['wimlib64'])
    
    # Extract
    extract_generic(
        r'{}\wimlib32.zip'.format(global_vars['TmpDir']),
        r'{}\wimlib\x32'.format(global_vars['CBinDir']))
    extract_generic(
        r'{}\wimlib64.zip'.format(global_vars['TmpDir']),
        r'{}\wimlib\x64'.format(global_vars['CBinDir']))
    
    # Cleanup
    remove_from_temp('wimlib32.zip')
    remove_from_temp('wimlib64.zip')

def update_xyplorer():
    # Stop running processes
    kill_process('XYplorerFree.exe')
    
    # Remove existing folders
    remove_from_kit('XYplorerFree')
    
    # Download
    download_to_temp('xyplorer_free.zip', SOURCE_URLS['XYplorerFree'])
    
    # Extract files
    extract_temp_to_cbin('xyplorer_free.zip', 'XYplorerFree')
    
    # Cleanup
    remove_from_temp('xyplorer_free.zip')

## Diagnostics ##
def update_aida64():
    # Stop running processes
    kill_process('notepadplusplus.exe')
    
    # Remove existing folders
    remove_from_kit('AIDA64')
    
    # Download
    download_to_temp('aida64.zip', SOURCE_URLS['AIDA64'])
    
    # Extract files
    extract_temp_to_cbin('aida64.zip', 'AIDA64')
    
    # Cleanup
    remove_from_temp('aida64.zip')

def update_autoruns():
    # Stop running processes
    kill_process('Autoruns.exe')
    kill_process('Autoruns64.exe')
    
    # Remove existing folders
    remove_from_kit('Autoruns')
    
    # Download
    download_to_temp('Autoruns.zip', SOURCE_URLS['Autoruns'])
    
    # Extract files
    extract_temp_to_cbin('Autoruns.zip', 'Autoruns')
    
    # Cleanup
    remove_from_temp('Autoruns.zip')

def update_bleachbit():
    # Stop running processes
    kill_process('bleachbit.exe')
    
    # Remove existing folders
    remove_from_kit('BleachBit')
    
    # Download
    download_to_temp('bleachbit.zip', SOURCE_URLS['BleachBit'])
    download_to_temp('Winapp2.zip', SOURCE_URLS['Winapp2'])
    
    # Extract files
    extract_temp_to_cbin('bleachbit.zip', 'BleachBit')
    extract_generic(
        r'{}\Winapp2.zip'.format(global_vars['TmpDir']),
        r'{}\BleachBit\cleaners'.format(global_vars['CBinDir']),
        mode='e', sz_args=[r'Winapp2-master\Non-CCleaner\Winapp2.ini'])
    
    # Move files into place
    dest = r'{}\BleachBit'.format(global_vars['CBinDir'])
    for item in os.scandir(r'{}\BleachBit-Portable'.format(dest)):
        dest_item = '{}\{}'.format(dest, item.name)
        if not os.path.exists(dest_item):
            shutil.move(item.path, dest_item)
    shutil.rmtree(
        r'{}\BleachBit\BleachBit-Portable'.format(global_vars['CBinDir']))
    
    # Cleanup
    remove_from_temp('bleachbit.zip')
    remove_from_temp('Winapp2.zip')

def update_bluescreenview():
    # Stop running processes
    for exe in ['BlueScreenView.exe', 'BlueScreenView64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('BlueScreenView')
    
    # Download
    download_to_temp('bluescreenview32.zip', SOURCE_URLS['BlueScreenView32'])
    download_to_temp('bluescreenview64.zip', SOURCE_URLS['BlueScreenView64'])
    
    # Extract files
    extract_temp_to_cbin('bluescreenview64.zip', 'BlueScreenView', sz_args=['BlueScreenView.exe'])
    shutil.move(
        r'{}\BlueScreenView\BlueScreenView.exe'.format(global_vars['CBinDir']),
        r'{}\BlueScreenView\BlueScreenView64.exe'.format(global_vars['CBinDir']))
    extract_temp_to_cbin('bluescreenview32.zip', 'BlueScreenView')
    
    # Cleanup
    remove_from_temp('bluescreenview32.zip')
    remove_from_temp('bluescreenview64.zip')

def update_erunt():
    # Stop running processes
    kill_process('ERUNT.EXE')
    
    # Remove existing folders
    remove_from_kit('ERUNT')
    
    # Download
    download_to_temp('erunt.zip', SOURCE_URLS['ERUNT'])
    
    # Extract files
    extract_temp_to_cbin('erunt.zip', 'ERUNT')
    
    # Cleanup
    remove_from_temp('erunt.zip')

def update_hitmanpro():
    # Stop running processes
    for exe in ['HitmanPro.exe', 'HitmanPro64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('HitmanPro')
    
    # Download
    dest = r'{}\HitmanPro'.format(global_vars['CBinDir'])
    download_generic(dest, 'HitmanPro.exe', SOURCE_URLS['HitmanPro32'])
    download_generic(dest, 'HitmanPro64.exe', SOURCE_URLS['HitmanPro64'])

def update_hwinfo():
    ## NOTE: Lives in .bin uncompressed
    # Stop running processes
    for exe in ['HWiNFO32.exe', 'HWiNFO64.exe']:
        kill_process(exe)
    
    # Download
    download_to_temp('HWiNFO.zip', SOURCE_URLS['HWiNFO'])
    
    # Extract files
    extract_temp_to_bin('HWiNFO.zip', 'HWiNFO')
    
    # Cleanup
    remove_from_temp('HWiNFO.zip')

def update_produkey():
    # Stop running processes
    for exe in ['ProduKey.exe', 'ProduKey64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('ProduKey')
    
    # Download
    download_to_temp('produkey32.zip', SOURCE_URLS['ProduKey32'])
    download_to_temp('produkey64.zip', SOURCE_URLS['ProduKey64'])
    
    # Extract files
    extract_temp_to_cbin('produkey64.zip', 'ProduKey', sz_args=['ProduKey.exe'])
    shutil.move(
        r'{}\ProduKey\ProduKey.exe'.format(global_vars['CBinDir']),
        r'{}\ProduKey\ProduKey64.exe'.format(global_vars['CBinDir']))
    extract_temp_to_cbin('produkey32.zip', 'ProduKey')
    
    # Cleanup
    remove_from_temp('produkey32.zip')
    remove_from_temp('produkey64.zip')

## Drivers ##
def update_intel_rst():
    # Remove existing folders
    remove_from_kit('Intel RST')
    
    # Prep
    dest = r'{}\_Drivers\Intel RST'.format(global_vars['CBinDir'])
    include_path = r'{}\_include\_Drivers\Intel RST'.format(
        global_vars['CBinDir'])
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    
    # Download
    for name, url in RST_SOURCES.items():
        download_generic(dest, name, url)

def update_intel_ssd_toolbox():
    # Remove existing folders
    remove_from_kit('Intel SSD Toolbox.exe')
    
    # Download
    download_generic(
        r'{}\_Drivers\Intel SSD Toolbox'.format(global_vars['CBinDir']),
        'Intel SSD Toolbox.exe',
        SOURCE_URLS['Intel SSD Toolbox'])

def update_samsung_magician():
    # Remove existing folders
    remove_from_kit('Samsung Magician.exe')
    
    # Download
    download_generic(
        r'{}\_Drivers\Samsung Magician'.format(global_vars['CBinDir']),
        'Samsung Magician.exe',
        SOURCE_URLS['Samsung Magician'])

def update_sdi_origin():
    # Download aria2
    download_to_temp('aria2.zip', SOURCE_URLS['aria2'])
    aria_source = r'{}\aria2.zip'.format(global_vars['TmpDir'])
    aria_dest = r'{}\aria2'.format(global_vars['TmpDir'])
    aria = r'{}\aria2c.exe'.format(aria_dest)
    extract_generic(aria_source, aria_dest, mode='e')
    
    # Prep for torrent download
    download_to_temp('sdio.torrent', SOURCE_URLS['SDIO Torrent'])
    sdio_torrent = r'{}\sdio.torrent'.format(global_vars['TmpDir'])
    out = run_program([aria, sdio_torrent, '-S'])
    indexes = []
    for line in out.stdout.decode().splitlines():
        r = re.search(r'^\s*(\d+)\|(.*)', line)
        if r and not re.search(r'(\.(bat|inf)|Video|Server|Printer|XP)', line, re.IGNORECASE):
            indexes.append(int(r.group(1)))
    indexes = [str(i) for i in sorted(indexes)]
    
    # Download SDI Origin
    cmd = [
        aria,
        '--select-file={}'.format(','.join(indexes)),
        '-d', aria_dest,
        '--seed-time=0',
        sdio_torrent,
        '-new_console:n', '-new_console:s33V',
        ]
    run_program(cmd, pipe=False, check=False, shell=True)
    sleep(1)
    wait_for_process('aria2c')
    
    # Download SDI Origin extra themes
    download_to_temp('sdio_themes.zip', SOURCE_URLS['SDIO Themes'])
    theme_source = r'{}\sdio_themes.zip'.format(global_vars['TmpDir'])
    theme_dest = r'{}\SDIO_Update\tools\SDI\themes'.format(aria_dest)
    extract_generic(theme_source, theme_dest)
    
    # Move files into place
    for item in os.scandir(r'{}\SDIO_Update'.format(aria_dest)):
        dest_item = '{}\_Drivers\SDIO\{}'.format(
            global_vars['BinDir'], item.name)
        r = re.search(r'^SDIO_x?(64|)_?R.*exe$', item.name, re.IGNORECASE)
        if r:
            dest_item = dest_item.replace(item.name, 'SDIO{}.exe'.format(
                r.group(1)))
        if (not os.path.exists(dest_item)
            and not re.search(r'\.(inf|bat)$', item.name, re.IGNORECASE)):
            shutil.move(item.path, dest_item)
    
    # Cleanup
    remove_from_temp('aria2')
    remove_from_temp('aria2.zip')
    remove_from_temp('sdio.torrent')
    remove_from_temp('sdio_themes.zip')

## Installers ##
def update_adobe_reader_dc():
    # Prep
    dest = r'{}\Installers\Extras\Office'.format(
        global_vars['BaseDir'])
    
    # Remove existing installer
    try:
        os.remove(r'{}\Adobe Reader DC.exe'.format(dest))
    except FileNotFoundError:
        pass
    
    # Download
    download_generic(
        dest, 'Adobe Reader DC.exe', SOURCE_URLS['Adobe Reader DC'])

def update_office():
    # Remove existing folders
    remove_from_kit('_Office')
    
    # Prep
    dest = r'{}\_Office'.format(global_vars['CBinDir'])
    include_path = r'{}\_include\_Office'.format(global_vars['CBinDir'])
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    
    # Download and extract
    for year in ['2013', '2016']:
        name = 'odt{}.exe'.format(year)
        url = 'Office Deployment Tool {}'.format(year)
        download_to_temp(name, SOURCE_URLS[url])
        cmd = [
            r'{}\odt{}.exe'.format(global_vars['TmpDir'], year),
            r'/extract:{}\{}'.format(global_vars['TmpDir'], year),
            '/quiet',
            ]
        run_program(cmd)
        shutil.move(
            r'{}\{}'.format(global_vars['TmpDir'], year),
            r'{}\_Office\{}'.format(global_vars['CBinDir'], year))
    
    # Cleanup
    remove_from_temp('odt2013.exe')
    remove_from_temp('odt2016.exe')

def update_classic_start_skin():
    # Remove existing folders
    remove_from_kit('ClassicStartSkin')
    
    # Download
    download_generic(
        r'{}\ClassicStartSkin'.format(global_vars['CBinDir']),
        'Metro-Win10-Black.skin7',
        SOURCE_URLS['ClassicStartSkin'])

def update_vcredists():
    # Remove existing folders
    remove_from_kit('_vcredists')
    
    # Prep
    dest = r'{}\_vcredists'.format(global_vars['CBinDir'])
    include_path = r'{}\_include\_vcredists'.format(global_vars['CBinDir'])
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    
    # Download
    for year in VCREDIST_SOURCES.keys():
        for bit in ['32', '64']:
            dest = r'{}\_vcredists\{}\x{}'.format(
                global_vars['CBinDir'], year, bit)
            download_generic(
                dest,
                'vcredist.exe',
                VCREDIST_SOURCES[year][bit])

def update_one_ninite(section, dest, name, url, indent=8, width=40):
    # Prep
    url = 'https://ninite.com/{}/ninite.exe'.format(url)
    
    # Download
    download_generic(out_dir=dest, out_name=name, source_url=url)
    
    # Copy to Installers folder
    installer_parent = r'{}\Installers\Extras\{}'.format(
        global_vars['BaseDir'], section)
    installer_dest = r'{}\{}'.format(installer_parent, name)
    os.makedirs(installer_parent, exist_ok=True)
    if os.path.exists(installer_dest):
        remove_item(installer_dest)
    shutil.copy(r'{}\{}'.format(dest, name), installer_dest)

def update_all_ninite(indent=8, width=40, other_results={}):
    print_info('{}Ninite'.format(' '*int(indent/2)))
    for section in sorted(NINITE_SOURCES.keys()):
        print_success('{}{}'.format(' '*int(indent/4*3), section))
        dest = r'{}\_Ninite\{}'.format(global_vars['CBinDir'], section)
        for name, url in sorted(NINITE_SOURCES[section].items()):
            try_and_print(message=name, function=update_one_ninite,
                other_results=other_results, indent=indent, width=width,
                section=section, dest=dest, name=name, url=url)

## Misc ##
def update_caffeine():
    # Stop running processes
    kill_process('caffeine.exe')
    
    # Remove existing folders
    remove_from_kit('Caffeine')
    
    # Download
    download_to_temp('caffeine.zip', SOURCE_URLS['Caffeine'])
    
    # Extract files
    extract_temp_to_cbin('caffeine.zip', 'Caffeine')
    
    # Cleanup
    remove_from_temp('caffeine.zip')

def update_du():
    # Stop running processes
    kill_process('du.exe')
    kill_process('du64.exe')
    
    # Remove existing folders
    remove_from_kit('Du')
    
    # Download
    download_to_temp('du.zip', SOURCE_URLS['Du'])
    
    # Extract files
    extract_temp_to_cbin('du.zip', 'Du')
    
    # Cleanup
    remove_from_temp('du.zip')

def update_everything():
    # Stop running processes
    for exe in ['Everything.exe', 'Everything64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('Everything')
    
    # Download
    download_to_temp('everything32.zip', SOURCE_URLS['Everything32'])
    download_to_temp('everything64.zip', SOURCE_URLS['Everything64'])
    
    # Extract files
    extract_temp_to_cbin('everything64.zip', 'Everything', sz_args=['Everything.exe'])
    shutil.move(
        r'{}\Everything\Everything.exe'.format(global_vars['CBinDir']),
        r'{}\Everything\Everything64.exe'.format(global_vars['CBinDir']))
    extract_temp_to_cbin('everything32.zip', 'Everything')
    
    # Cleanup
    remove_from_temp('everything32.zip')
    remove_from_temp('everything64.zip')

def update_firefox_ublock_origin():
    # Remove existing folders
    remove_from_kit('FirefoxExtensions')
    
    # Download
    download_to_temp('ff-uBO.xpi', SOURCE_URLS['Firefox uBO'])
    
    # Extract files
    extract_generic(
        r'{}\ff-uBO.xpi'.format(global_vars['TmpDir']),
        r'{}\FirefoxExtensions\uBlock0@raymondhill.net'.format(
            global_vars['CBinDir']))
    
    # Cleanup
    remove_from_temp('ff-uBO.xpi')

def update_notepadplusplus():
    # Stop running processes
    kill_process('notepadplusplus.exe')
    
    # Remove existing folders
    remove_from_kit('NotepadPlusPlus')
    
    # Download
    download_to_temp('npp.7z', SOURCE_URLS['NotepadPlusPlus'])
    
    # Extract files
    extract_temp_to_cbin('npp.7z', 'NotepadPlusPlus')
    shutil.move(
        r'{}\NotepadPlusPlus\notepad++.exe'.format(global_vars['CBinDir']),
        r'{}\NotepadPlusPlus\notepadplusplus.exe'.format(global_vars['CBinDir'])
        )
    
    # Cleanup
    remove_from_temp('npp.7z')

def update_putty():
    # Stop running processes
    kill_process('PUTTY.EXE')
    
    # Remove existing folders
    remove_from_kit('PuTTY')
    
    # Download
    download_to_temp('putty.zip', SOURCE_URLS['PuTTY'])
    
    # Extract files
    extract_temp_to_cbin('putty.zip', 'PuTTY')
    
    # Cleanup
    remove_from_temp('putty.zip')

def update_wiztree():
    # Stop running processes
    for process in ['WizTree.exe', 'WizTree64.exe']:
        kill_process(process)
    
    # Remove existing folders
    remove_from_kit('WizTree')
    
    # Download
    download_to_temp(
        'wiztree.zip', SOURCE_URLS['WizTree'])
    
    # Extract files
    extract_temp_to_cbin('wiztree.zip', 'WizTree')
    
    # Cleanup
    remove_from_temp('wiztree.zip')

def update_xmplay():
    # Stop running processes
    kill_process('xmplay.exe')
    
    # Remove existing folders
    remove_from_kit('XMPlay')
    
    # Download
    download_to_temp('xmplay.zip', SOURCE_URLS['XMPlay'])
    download_to_temp('xmp-7z.zip', SOURCE_URLS['XMPlay 7z'])
    download_to_temp('xmp-gme.zip', SOURCE_URLS['XMPlay Game'])
    download_to_temp('xmp-rar.zip', SOURCE_URLS['XMPlay RAR'])
    download_to_temp('WAModern.zip', SOURCE_URLS['XMPlay WAModern'])
    
    # Extract files
    extract_temp_to_cbin('xmplay.zip', 'XMPlay',
        mode='e', sz_args=['xmplay.exe', 'xmplay.txt'])
    for item in ['xmp-7z', 'xmp-gme', 'xmp-rar', 'WAModern']:  
        filter = []
        if item == 'WAModern':
            filter.append('WAModern NightVision.xmpskin')
        extract_generic(
            r'{}\{}.zip'.format(global_vars['TmpDir'], item),
            r'{}\XMPlay\plugins'.format(global_vars['CBinDir']),
            mode='e', sz_args=filter)
    
    # Download Music
    dest = r'{}\XMPlay\music_tmp\MOD'.format(global_vars['CBinDir'])
    for mod in MUSIC_MOD:
        name = mod.split('#')[-1]
        url = 'https://api.modarchive.org/downloads.php?moduleid={}'.format(mod)
        download_generic(dest, name, url)
    dest = r'{}\XMPlay\music_tmp\SNES'.format(global_vars['CBinDir'])
    for game in MUSIC_SNES:
        name = '{}.rsn'.format(game)
        url = 'http://snesmusic.org/v2/download.php?spcNow={}'.format(game)
        download_generic(dest, name, url)
    
    # Compress Music
    cmd = [
        global_vars['Tools']['SevenZip'],
        'a', r'{}\XMPlay\music.7z'.format(global_vars['CBinDir']),
        '-t7z', '-mx=9', '-bso0', '-bse0',
        r'{}\XMPlay\music_tmp\*'.format(global_vars['CBinDir']),
        ]
    run_program(cmd)
    
    # Cleanup
    remove_item(r'{}\XMPlay\music_tmp'.format(global_vars['CBinDir']))
    remove_from_temp('xmplay.zip')
    remove_from_temp('xmp-7z.zip')
    remove_from_temp('xmp-gme.zip')
    remove_from_temp('xmp-rar.zip')
    remove_from_temp('WAModern.zip')

## Repairs ##
def update_adwcleaner():
    # Stop running processes
    kill_process('AdwCleaner.exe')
    
    # Remove existing folders
    remove_from_kit('AdwCleaner')
    
    # Download
    url = resolve_dynamic_url(
        SOURCE_URLS['AdwCleaner'],
        'id="downloadLink"')
    download_generic(
        r'{}\AdwCleaner'.format(global_vars['CBinDir']), 'AdwCleaner.exe', url)

def update_kvrt():
    # Stop running processes
    kill_process('KVRT.exe')
    
    # Remove existing folders
    remove_from_kit('KVRT')
    
    # Download
    download_generic(
        r'{}\KVRT'.format(global_vars['CBinDir']),
        'KVRT.exe',
        SOURCE_URLS['KVRT'])

def update_rkill():
    # Stop running processes
    kill_process('RKill.exe')
    
    # Remove existing folders
    remove_from_kit('RKill')
    
    # Download
    url = resolve_dynamic_url(
        SOURCE_URLS['RKill'],
        'href.*rkill\.exe')
    download_generic(
        r'{}\RKill'.format(global_vars['CBinDir']), 'RKill.exe', url)

def update_tdsskiller():
    # Stop running processes
    kill_process('TDSSKiller.exe')
    
    # Remove existing folders
    remove_from_kit('TDSSKiller')
    
    # Download
    download_generic(
        r'{}\TDSSKiller'.format(global_vars['CBinDir']),
        'TDSSKiller.exe',
        SOURCE_URLS['TDSSKiller'])

## Uninstallers ##
def update_iobit_uninstaller():
    # Stop running processes
    kill_process('IObitUninstallerPortable.exe')
    
    # Remove existing folders
    remove_from_kit('IObitUninstallerPortable')
    
    # Download
    download_generic(
        global_vars['CBinDir'],
        'IObitUninstallerPortable.exe',
        SOURCE_URLS['IOBit_Uninstaller'])
    
    # "Install"
    cmd = r'{}\IObitUninstallerPortable.exe'.format(global_vars['CBinDir'])
    popen_program(cmd)
    sleep(1)
    wait_for_process('IObitUninstallerPortable')
    
    # Cleanup
    remove_from_kit('IObitUninstallerPortable.exe')

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
