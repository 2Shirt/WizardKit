# Wizard Kit: Functions - Build / Update
## NOTE: This file is full of magic strings!

import requests

from functions.common import *
from settings.launchers import *

NINITE_FILES = {
    'Bundles': {
        'Runtimes.exe': '.net4.7-air-java8-silverlight',
        'Legacy.exe': '.net4.7-7zip-air-chrome-firefox-java8-silverlight-vlc',
        'Modern.exe': '.net4.7-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc',
        },
    'Audio-Video': {
        'AIMP.exe': 'aimp',
        'Audacity.exe': 'audacity',
        'CCCP.exe': 'cccp',
        'Foobar2000.exe': 'foobar',
        'GOM.exe': 'gom',
        'HandBrake.exe': 'handbrake',
        'iTunes.exe': 'itunes',
        'K-Lite Codecs.exe': 'klitecodecs',
        'MediaMonkey.exe': 'mediamonkey',
        'MusicBee.exe': 'musicbee',
        'Spotify.exe': 'spotify',
        'VLC.exe': 'vlc',
        'Winamp.exe': 'winamp',
        },
    'Cloud Storage': {
        'Dropbox.exe': 'dropbox',
        'Google Backup & Sync.exe': 'googlebackupandsync',
        'Mozy.exe': 'mozy',
        'OneDrive.exe': 'onedrive',
        'SugarSync.exe': 'sugarsync',
        },
    'Communication': {
        'Pidgin.exe': 'pidgin',
        'Skype.exe': 'skype',
        'Trillian.exe': 'trillian',
        },
    'Compression': {
        '7-Zip.exe': '7zip',
        'PeaZip.exe': 'peazip',
        'WinRAR.exe': 'winrar',
        },
    'Developer': {
        'Eclipse.exe': 'eclipse',
        'FileZilla.exe': 'filezilla',
        'JDK 8.exe': 'jdk8',
        'JDK 8 (x64).exe': 'jdkx8',
        'Notepad++.exe': 'notepadplusplus',
        'PuTTY.exe': 'putty',
        'Python 2.exe': 'python',
        'Visual Studio Code.exe': 'vscode',
        'WinMerge.exe': 'winmerge',
        'WinSCP.exe': 'winscp',
        },
    'File Sharing': {
        'qBittorrent.exe': 'qbittorrent',
        },
    'Image-Photo': {
        'Blender.exe': 'blender',
        'FastStone.exe': 'faststone',
        'GIMP.exe': 'gimp',
        'Greenshot.exe': 'greenshot',
        'Inkscape.exe': 'inkscape',
        'IrfanView.exe': 'irfanview',
        'Krita.exe': 'krita',
        'Paint.NET.exe': 'paint.net',
        'ShareX.exe': 'sharex',
        'XnView.exe': 'xnview',
        },
    'Misc': {
        'Evernote.exe': 'evernote',
        'Everything.exe': 'everything',
        'KeePass 2.exe': 'keepass2',
        'Google Earth.exe': 'googleearth',
        'NV Access.exe': 'nvda',
        'Steam.exe': 'steam',
        },
    'Office': {
        'CutePDF.exe': 'cutepdf',
        'Foxit Reader.exe': 'foxit',
        'LibreOffice.exe': 'libreoffice',
        'OpenOffice.exe': 'openoffice',
        'PDFCreator.exe': 'pdfcreator',
        'SumatraPDF.exe': 'sumatrapdf',
        'Thunderbird.exe': 'thunderbird',
        },
    'Runtimes': {
        'Adobe Air.exe': 'air',
        'dotNET.exe': '.net4.7',
        'Java 8.exe': 'java8',
        'Shockwave.exe': 'shockwave',
        'Silverlight.exe': 'silverlight',
        },
    'Security': {
        'Avast.exe': 'avast',
        'AVG.exe': 'avg',
        'Avira.exe': 'avira',
        'Microsoft Security Essentials.exe': 'essentials',
        'Malwarebytes Anti-Malware.exe': 'malwarebytes',
        'Spybot 2.exe': 'spybot2',
        'SUPERAntiSpyware.exe': 'super',
        },
    'Utilities': {
        'CDBurnerXP.exe': 'cdburnerxp',
        'Classic Start.exe': 'classicstart',
        'Glary Utilities.exe': 'glary',
        'ImgBurn.exe': 'imgburn',
        'InfraRecorder.exe': 'infrarecorder',
        'Launchy.exe': 'launchy',
        'RealVNC.exe': 'realvnc',
        'Revo Uninstaller.exe': 'revo',
        'TeamViewer 12.exe': 'teamviewer12',
        'TeraCopy.exe': 'teracopy',
        'WinDirStat.exe': 'windirstat',
        },
    'Web Browsers': {
        'Google Chrome.exe': 'chrome',
        'Mozilla Firefox.exe': 'firefox',
        'Opera Chromium.exe': 'operaChromium',
        },
    }
RST_FILES = {
    #SetupRST_12.0.exe :  Removed from download center?
    #SetupRST_12.5.exe :  Removed from download center?
    #SetupRST_12.8.exe :  Removed from download center?
    'SetupRST_12.9.exe': 'https://downloadmirror.intel.com/23496/eng/SetupRST.exe',
    #SetupRST_13.x.exe :  Broken, doesn't support > .NET 4.5
    'SetupRST_14.0.exe': 'https://downloadmirror.intel.com/25091/eng/SetupRST.exe',
    'SetupRST_14.8.exe': 'https://downloadmirror.intel.com/26759/eng/setuprst.exe',
    'SetupRST_15.8.exe': 'https://downloadmirror.intel.com/27147/eng/SetupRST.exe',
    }

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
    download_generic(global_vars['TmpDir'], out_name, source_url)

def resolve_dynamic_url(source_url, regex, tmp_file='webpage.tmp'):
    """Scan source_url for a url using the regex provided; returns str."""
    # Download the "download page"
    try:
        download_to_temp('webpage.tmp', source_url)
    except Exception:
        # "Fail silently as the download_to_temp() function will catch it
        return None

    # Scan the file for the regex
    tmp_file = r'{}\{}'.format(global_vars['TmpDir'], tmp_file)
    with open(tmp_file, 'r') as file:
        for line in file:
            if re.search(regex, line):
                url = line.strip()
                url = re.sub(r'.*(a |)href="([^"]+)".*', r'\2', url)
                url = re.sub(r".*(a |)href='([^']+)'.*", r'\2', url)
                break

    # Cleanup and return
    os.remove(tmp_file)
    return url

def extract_generic(source, dest, mode='x', sz_args=[]):
    cmd = [
        global_vars['Tools']['SevenZip'],
        mode, source, r'-o{}'.format(dest),
        '-aoa', '-bso0', '-bse0',
        ]
    cmd.extend(sz_args)
    run_program(cmd)

def extract_temp_to_bin(source, item, mode='x', sz_args=[]):
    source = r'{}\{}'.format(global_vars['TmpDir'], source)
    dest = r'{}\{}'.format(global_vars['BinDir'], item)
    extract_generic(source, dest, mode, sz_args)

def extract_temp_to_cbin(source, item, mode='x', sz_args=[]):
    source = r'{}\{}'.format(global_vars['TmpDir'], source)
    dest = r'{}\{}'.format(global_vars['CBinDir'], item)
    include_path = r'{}\_include\{}'.format(global_vars['CBinDir'], item)
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    extract_generic(source, dest, mode, sz_args)

def remove_from_kit(item):
    item_locations = []
    for p in [global_vars['BinDir'], global_vars['CBinDir']]:
        item_locations.append(r'{}\{}'.format(p, item))
        item_locations.append(r'{}\_Drivers\{}'.format(p, item))
    for item_path in item_locations:
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)
            else:
                os.remove(item_path)

def remove_from_temp(item):
    os.remove(r'{}\{}'.format(global_vars['TmpDir'], item))

## Data Recovery ##
def update_testdisk():
    # Stop running processes
    for exe in ['fidentify_win.exe', 'photorec_win.exe',
        'qphotorec_win.exe', 'testdisk_win.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('TestDisk')
    
    # Download
    name = 'testdisk_wip.zip'
    url = 'https://www.cgsecurity.org/testdisk-7.1-WIP.win.zip'
    download_to_temp(name, url)
    
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
    name = 'FastCopy32.zip'
    url = 'http://ftp.vector.co.jp/69/28/2323/FastCopy332.zip'
    download_to_temp(name, url)

    name = 'FastCopy64.zip'
    url = 'http://ftp.vector.co.jp/69/28/2323/FastCopy332_x64.zip'
    download_to_temp(name, url)
    
    # Extract
    extract_temp_to_bin('FastCopy64.zip', 'FastCopy', sz_args=['FastCopy.exe'])
    shutil.move(
        r'{}\FastCopy\FastCopy.exe'.format(global_vars['BinDir']),
        r'{}\FastCopy\FastCopy64.exe'.format(global_vars['BinDir']))
    extract_temp_to_bin('FastCopy32.zip', 'FastCopy', sz_args=[r'-x!setup.exe', r'-x!*.dll'])
    
    # Cleanup
    remove_from_temp('FastCopy32.zip')
    remove_from_temp('FastCopy64.zip')

def update_xyplorer():
    # Stop running processes
    kill_process('XYplorerFree.exe')
    
    # Remove existing folders
    remove_from_kit('XYplorerFree')
    
    # Download
    name = 'xyplorer_free.zip'
    url = 'https://www.xyplorer.com/download/xyplorer_free_noinstall.zip'
    download_to_temp(name, url)
    
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
    name = 'aida64.zip'
    url = 'http://download.aida64.com/aida64engineer592.zip'
    download_to_temp(name, url)
    
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
    name = 'Autoruns.zip'
    url = 'https://download.sysinternals.com/files/Autoruns.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('Autoruns.zip', 'Autoruns')
    
    # Cleanup
    remove_from_temp('Autoruns.zip')

def update_bleachbit():
    # Stop running processes
    kill_process('bleachbit.exe')
    
    # Remove existing folders
    remove_from_kit('BleachBit-Portable')
    
    # Download
    name = 'BleachBit-Portable.zip'
    url = 'https://download.bleachbit.org/beta/1.17/BleachBit-1.17-portable.zip'
    download_to_temp(name, url)
    name = 'Winapp2.zip'
    url = 'https://github.com/MoscaDotTo/Winapp2/archive/master.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('BleachBit-Portable.zip', 'BleachBit-Portable')
    extract_generic(
        r'{}\Winapp2.zip'.format(global_vars['TmpDir']),
        r'{}\BleachBit-Portable\cleaners'.format(global_vars['CBinDir']),
        mode='e', sz_args=[r'Winapp2-master\Non-CCleaner\Winapp2.ini'])
    
    # Move files into place
    dest = r'{}\BleachBit-Portable'.format(global_vars['CBinDir'])
    for item in os.scandir(r'{}\BleachBit-Portable'.format(dest)):
        dest_item = '{}\{}'.format(dest, item.name)
        if not os.path.exists(dest_item):
            shutil.move(item.path, dest_item)
    shutil.rmtree(
        r'{}\BleachBit-Portable\BleachBit-Portable'.format(global_vars['CBinDir']))
    
    # Cleanup
    remove_from_temp('BleachBit-Portable.zip')
    remove_from_temp('Winapp2.zip')

def update_bluescreenview():
    # Stop running processes
    for exe in ['BlueScreenView.exe', 'BlueScreenView64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('BlueScreenView')
    
    # Download
    name = 'bluescreenview.zip'
    url = 'http://www.nirsoft.net/utils/bluescreenview.zip'
    download_to_temp(name, url)
    
    name = 'bluescreenview64.zip'
    url = 'http://www.nirsoft.net/utils/bluescreenview-x64.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('bluescreenview64.zip', 'BlueScreenView', sz_args=['BlueScreenView.exe'])
    shutil.move(
        r'{}\BlueScreenView\BlueScreenView.exe'.format(global_vars['CBinDir']),
        r'{}\BlueScreenView\BlueScreenView64.exe'.format(global_vars['CBinDir']))
    extract_temp_to_cbin('bluescreenview.zip', 'BlueScreenView')
    
    # Cleanup
    remove_from_temp('bluescreenview.zip')
    remove_from_temp('bluescreenview64.zip')

def update_du():
    # Stop running processes
    kill_process('du.exe')
    kill_process('du64.exe')
    
    # Remove existing folders
    remove_from_kit('Du')
    
    # Download
    name = 'du.zip'
    url = 'https://download.sysinternals.com/files/DU.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('du.zip', 'Du')
    
    # Cleanup
    remove_from_temp('du.zip')

def update_erunt():
    # Stop running processes
    kill_process('ERUNT.EXE')
    
    # Remove existing folders
    remove_from_kit('ERUNT')
    
    # Download
    name = 'erunt.zip'
    url = 'http://www.aumha.org/downloads/erunt.zip'
    download_to_temp(name, url)
    
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
    name = 'HitmanPro.exe'
    url = 'https://dl.surfright.nl/HitmanPro.exe'
    download_generic(dest, name, url)
    
    name = 'HitmanPro64.exe'
    url = 'https://dl.surfright.nl/HitmanPro_x64.exe'
    download_generic(dest, name, url)

def update_hwinfo():
    ## NOTE: Lives in .bin uncompressed
    # Stop running processes
    for exe in ['HWiNFO32.exe', 'HWiNFO64.exe']:
        kill_process(exe)
    
    # Download
    name = 'HWiNFO32.zip'
    url = 'http://app.oldfoss.com:81/download/HWiNFO/hw32_560.zip'
    download_to_temp(name, url)

    name = 'HWiNFO64.zip'
    url = 'http://app.oldfoss.com:81/download/HWiNFO/hw64_560.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_bin('HWiNFO32.zip', 'HWiNFO')
    extract_temp_to_bin('HWiNFO64.zip', 'HWiNFO')
    
    # Cleanup
    remove_from_temp('HWiNFO32.zip')
    remove_from_temp('HWiNFO64.zip')

def update_produkey():
    # Stop running processes
    for exe in ['ProduKey.exe', 'ProduKey64.exe']:
        kill_process(exe)
    
    # Remove existing folders
    remove_from_kit('ProduKey')
    
    # Download
    name = 'produkey.zip'
    url = 'http://www.nirsoft.net/utils/produkey.zip'
    download_to_temp(name, url)
    
    name = 'produkey64.zip'
    url = 'http://www.nirsoft.net/utils/produkey-x64.zip'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('produkey64.zip', 'ProduKey', sz_args=['ProduKey.exe'])
    shutil.move(
        r'{}\ProduKey\ProduKey.exe'.format(global_vars['CBinDir']),
        r'{}\ProduKey\ProduKey64.exe'.format(global_vars['CBinDir']))
    extract_temp_to_cbin('produkey.zip', 'ProduKey')
    
    # Cleanup
    remove_from_temp('produkey.zip')
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
    for name, url in RST_FILES.items():
        download_generic(dest, name, url)

def update_intel_ssd_toolbox():
    # Remove existing folders
    remove_from_kit('Intel SSD Toolbox.exe')
    
    # Download
    dest = r'{}\_Drivers'.format(global_vars['CBinDir'])
    name = 'Intel SSD Toolbox.exe'
    url = r'https://downloadmirror.intel.com/27330/eng/Intel%20SSD%20Toolbox%20-%20v3.4.9.exe'
    download_generic(dest, name, url)

def update_samsung_magician():
    # Remove existing folders
    remove_from_kit('Samsung Magician.exe')
    
    # Download
    dest = r'{}\_Drivers'.format(global_vars['CBinDir'])
    name = 'Samsung Magician.exe'
    url = 'http://downloadcenter.samsung.com/content/SW/201710/20171019164455812/Samsung_Magician_Installer.exe'
    download_generic(dest, name, url)

def update_sdi():
    #TODO
    pass

## Installers ##
def update_adobe_reader_dc():
    pass
    
## Misc ##
def update_everything():
    pass

def update_notepadplusplus():
    # Stop running processes
    kill_process('notepadplusplus.exe')
    
    # Remove existing folders
    remove_from_kit('NotepadPlusPlus')
    
    # Download
    name = 'npp.7z'
    url = 'https://notepad-plus-plus.org/repository/7.x/7.5.1/npp.7.5.1.bin.minimalist.7z'
    download_to_temp(name, url)
    
    # Extract files
    extract_temp_to_cbin('npp.7z', 'NotepadPlusPlus')
    shutil.move(
        r'{}\NotepadPlusPlus\notepad++.exe'.format(global_vars['CBinDir']),
        r'{}\NotepadPlusPlus\notepadplusplus.exe'.format(global_vars['CBinDir'])
        )
    
    # Cleanup
    remove_from_temp('npp.7z')

def update_treesizefree():
    pass

def update_xmplay():
    pass

## Repairs ##
def update_adwcleaner():
    #def update_adwcleaner():
    #    path = global_vars['BinDir']
    #    name = 'AdwCleaner.exe'
    #    _dl_page = 'http://www.bleepingcomputer.com/download/adwcleaner/dl/125/'
    #    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/a/adwcleaner/AdwCleaner\.exe'
    #    url = resolve_dynamic_url(_dl_page, _regex)
    #    download_to_temp(path, name, url)
    #
    pass

def update_kvrt():
    #def update_kvrt():
    #    path = global_vars['BinDir']
    #    name = 'KVRT.exe'
    #    url = 'http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe'
    #    download_to_temp(path, name, url)
    pass

def update_rkill():
    #def update_rkill():
    #    path = '{BinDir}/RKill'.format(**global_vars)
    #    name = 'RKill.exe'
    #    _dl_page = 'http://www.bleepingcomputer.com/download/rkill/dl/10/'
    #    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/r/rkill/rkill\.exe'
    #    url = resolve_dynamic_url(_dl_page, _regex)
    #    download_to_temp(path, name, url)
    pass

def update_tdsskiller():
    #def update_tdsskiller():
    #    path = global_vars['BinDir']
    #    name = 'TDSSKiller.exe'
    #    url = 'http://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe'
    #    download_to_temp(path, name, url)
    pass

## Uninstallers ##
def update_iobit_uninstaller():
    pass

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
