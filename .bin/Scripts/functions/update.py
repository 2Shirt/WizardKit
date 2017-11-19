# Wizard Kit: Functions - Build / Update
## NOTE: This file is full of magic strings!

import requests

from functions.common import *
from settings.launchers import *

def download_to_temp(out_name, source_url):
    """Downloads a file using requests."""
    ## Code based on this Q&A: https://stackoverflow.com/q/16694907
    ### Asked by: https://stackoverflow.com/users/427457/roman-podlinov
    ### Edited by: https://stackoverflow.com/users/657427/christophe-roussy
    ### Using answer: https://stackoverflow.com/a/39217788
    ### Answer from: https://stackoverflow.com/users/4323/john-zwinck
    out_dir = global_vars['TmpDir']
    os.makedirs(out_dir, exist_ok=True)
    out_path = '{}/{}'.format(out_dir, out_name)
    try:
        r = requests.get(source_url, stream=True)
        with open(out_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        r.close()
    except:
        raise GenericError('Failed to download file.')

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

def extract_from_temp(source, root, dest, *args):
    cmd = [
        global_vars['Tools']['SevenZip'],
        'e', r'{}\{}'.format(global_vars['TmpDir'], source),
        r'-o{}\{}'.format(root, dest),
        '-aoa', '-bso0', '-bse0',
        ]
    cmd.extend(args)
    run_program(cmd)

def extract_to_bin(source, item, *args):
    extract_from_temp(source, global_vars['BinDir'], item, *args)

def extract_to_cbin(source, item, *args):
    dest = r'{}\{}'.format(global_vars['CBinDir'], item)
    include_path = r'{}\_include\{}'.format(global_vars['CBinDir'], item)
    if os.path.exists(include_path):
        shutil.copytree(include_path, dest)
    extract_from_temp(source, global_vars['CBinDir'], item, *args)

def remove_from_kit(item):
    bin_path = r'{}\{}'.format(global_vars['BinDir'], item)
    cbin_path = r'{}\{}'.format(global_vars['CBinDir'], item)
    shutil.rmtree(bin_path, ignore_errors=True)
    shutil.rmtree(cbin_path, ignore_errors=True)

def remove_from_temp(item):
    os.remove(r'{}\{}'.format(global_vars['TmpDir'], item))

## .bin (NOT compressed) ##
def update_fastcopy():
    # Stop running processes
    for process in ['FastCopy.exe', 'FastCopy64.exe']:
        kill_process(process)
    
    # Download
    name = 'FastCopy32.zip'
    url = 'http://ftp.vector.co.jp/69/28/2323/FastCopy332.zip'
    download_to_temp(name, url)

    name = 'FastCopy64.zip'
    url = 'http://ftp.vector.co.jp/69/28/2323/FastCopy332_x64.zip'
    download_to_temp(name, url)
    
    # Extract
    extract_to_bin('FastCopy64.zip', 'FastCopy', 'FastCopy.exe')
    shutil.move(
        r'{}\FastCopy\FastCopy.exe'.format(global_vars['BinDir']),
        r'{}\FastCopy\FastCopy64.exe'.format(global_vars['BinDir']))
    extract_to_bin('FastCopy32.zip', 'FastCopy', r'-x!setup.exe', r'-x!*.dll')
    
    # Cleanup
    remove_from_temp('FastCopy32.zip')
    remove_from_temp('FastCopy64.zip')

def update_hwinfo():
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
    extract_to_bin('HWiNFO32.zip', 'HWiNFO')
    extract_to_bin('HWiNFO64.zip', 'HWiNFO')
    
    # Cleanup
    remove_from_temp('HWiNFO32.zip')
    remove_from_temp('HWiNFO64.zip')

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
    extract_to_cbin('testdisk_wip.zip', 'TestDisk')
    
    # Cleanup
    remove_from_temp('testdisk_wip.zip')

## Data Transfers ##
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
    extract_to_cbin('xyplorer_free.zip', 'XYplorerFree')
    
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
    extract_to_cbin('aida64.zip', 'AIDA64')
    
    # Cleanup
    remove_from_temp('aida64.zip')

def update_autoruns():
    pass

def update_bleachbit():
    pass

def update_bluescreenview():
    pass

def update_du():
    pass

def update_erunt():
    pass

def update_hitmanpro():
    #def download_hitmanpro():
    #    path = '{CBinDir}/HitmanPro'.format(**global_vars)
    #    name = 'HitmanPro.exe'
    #    url = 'http://dl.surfright.nl/HitmanPro.exe'
    #    download_to_temp(path, name, url)
    #
    #    name = 'HitmanPro64.exe'
    #    url = 'http://dl.surfright.nl/HitmanPro_x64.exe'
    #    download_to_temp(path, name, url)
    #
    pass

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
    extract_to_cbin('produkey64.zip', 'ProduKey', 'ProduKey.exe')
    shutil.move(
        r'{}\ProduKey\ProduKey.exe'.format(global_vars['CBinDir']),
        r'{}\ProduKey\ProduKey64.exe'.format(global_vars['CBinDir']))
    extract_to_cbin('produkey.zip', 'ProduKey')
    
    # Cleanup
    remove_from_temp('produkey.zip')
    remove_from_temp('produkey64.zip')

## Drivers ##
def update_intel_rst():
    pass

def update_intel_ssd_toolbox():
    #def update_intel_ssd_toolbox():
    #    path = '{BinDir}/_Drivers'.format(**global_vars)
    #    name = 'Intel SSD Toolbox.exe'
    #    _dl_page = 'https://downloadcenter.intel.com/download/26085/Intel-Solid-State-Drive-Toolbox'
    #    _regex = r'href=./downloads/eula/[0-9]+/Intel-Solid-State-Drive-Toolbox.httpDown=https\%3A\%2F\%2Fdownloadmirror\.intel\.com\%2F[0-9]+\%2Feng\%2FIntel\%20SSD\%20Toolbox\%20-\%20v[0-9\.]+.exe'
    #    url = resolve_dynamic_url(_dl_page, _regex)
    #    url = re.sub(r'.*httpDown=(.*)', r'\1', url, re.IGNORECASE)
    #    url = url.replace('%3A', ':')
    #    url = url.replace('%2F', '/')
    #    download_to_temp(path, name, url)
    pass

def update_samsing_magician():
    #def update_samsung_magician():
    #    print_warning('Disabled.')
    #    #~Broken~# path = '{BinDir}/_Drivers'.format(**global_vars)
    #    #~Broken~# name = 'Samsung Magician.zip'
    #    #~Broken~# _dl_page = 'http://www.samsung.com/semiconductor/minisite/ssd/download/tools.html'
    #    #~Broken~# _regex = r'href=./semiconductor/minisite/ssd/downloads/software/Samsung_Magician_Setup_v[0-9]+.zip'
    #    #~Broken~# url = resolve_dynamic_url(_dl_page, _regex)
    #    #~Broken~# # Convert relative url to absolute
    #    #~Broken~# url = 'http://www.samsung.com' + url
    #    #~Broken~# download_to_temp(path, name, url)
    #    #~Broken~# # Extract and replace old copy
    #    #~Broken~# _args = [
    #    #~Broken~#     'e', '"{BinDir}/_Drivers/Samsung Magician.zip"'.format(**global_vars),
    #    #~Broken~#     '-aoa', '-bso0', '-bsp0',
    #    #~Broken~#     '-o"{BinDir}/_Drivers"'.format(**global_vars)
    #    #~Broken~# ]
    #    #~Broken~# run_program(seven_zip, _args)
    #    #~Broken~# try:
    #    #~Broken~#     os.remove('{BinDir}/_Drivers/Samsung Magician.zip'.format(**global_vars))
    #    #~Broken~#     #~PoSH~# Move-Item "$bin\_Drivers\Samsung*exe" "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null
    #    #~Broken~# except Exception:
    #    #~Broken~#     pass
    #    pass
    pass

def update_sdi():
    pass

## Installers ##
def update_adobe_reader():
    pass
    
def update_ninite():
    # Ninite - Bundles
    # print_info('Installers')
    # print_success(' '*4 + 'Ninite Bundles')
    # _path = r'{BaseDir}\Installers\Extras\Bundles'.format(**global_vars)
    # try_and_print(message='Runtimes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Runtimes.exe', source_url='https://ninite.com/.net4.7-air-java8-silverlight/ninite.exe')
    # try_and_print(message='Legacy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Legacy.exe', source_url='https://ninite.com/.net4.7-7zip-air-chrome-firefox-java8-silverlight-vlc/ninite.exe')
    # try_and_print(message='Modern.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Modern.exe', source_url='https://ninite.com/.net4.7-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc/ninite.exe')
        
    # # Ninite - Audio-Video
    # print_success(' '*4 + 'Audio-Video')
    # _path = r'{BaseDir}\Installers\Extras\Audio-Video'.format(**global_vars)
    # try_and_print(message='AIMP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='AIMP.exe', source_url='https://ninite.com/aimp/ninite.exe')
    # try_and_print(message='Audacity.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Audacity.exe', source_url='https://ninite.com/audacity/ninite.exe')
    # try_and_print(message='CCCP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CCCP.exe', source_url='https://ninite.com/cccp/ninite.exe')
    # try_and_print(message='Foobar2000.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Foobar2000.exe', source_url='https://ninite.com/foobar/ninite.exe')
    # try_and_print(message='GOM.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='GOM.exe', source_url='https://ninite.com/gom/ninite.exe')
    # try_and_print(message='iTunes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='HandBrake.exe', source_url='https://ninite.com/handbrake/ninite.exe')
    # try_and_print(message='iTunes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='iTunes.exe', source_url='https://ninite.com/itunes/ninite.exe')
    # try_and_print(message='K-Lite Codecs.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='K-Lite Codecs.exe', source_url='https://ninite.com/klitecodecs/ninite.exe')
    # try_and_print(message='MediaMonkey.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='MediaMonkey.exe', source_url='https://ninite.com/mediamonkey/ninite.exe')
    # try_and_print(message='MusicBee.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='MusicBee.exe', source_url='https://ninite.com/musicbee/ninite.exe')
    # try_and_print(message='Spotify.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Spotify.exe', source_url='https://ninite.com/spotify/ninite.exe')
    # try_and_print(message='VLC.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='VLC.exe', source_url='https://ninite.com/vlc/ninite.exe')
    # try_and_print(message='Winamp.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Winamp.exe', source_url='https://ninite.com/winamp/ninite.exe')

    # # Ninite - Cloud Storage
    # print_success(' '*4 + 'Cloud Storage')
    # _path = r'{BaseDir}\Installers\Extras\Cloud Storage'.format(**global_vars)
    # try_and_print(message='Dropbox.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Dropbox.exe', source_url='https://ninite.com/dropbox/ninite.exe')
    # try_and_print(message='Google Backup & Sync.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Backup & Sync.exe', source_url='https://ninite.com/googlebackupandsync/ninite.exe')
    # try_and_print(message='Mozy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Mozy.exe', source_url='https://ninite.com/mozy/ninite.exe')
    # try_and_print(message='OneDrive.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='OneDrive.exe', source_url='https://ninite.com/onedrive/ninite.exe')
    # try_and_print(message='SugarSync.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SugarSync.exe', source_url='https://ninite.com/sugarsync/ninite.exe')

    # # Ninite - Communication
    # print_success(' '*4 + 'Communication')
    # _path = r'{BaseDir}\Installers\Extras\Communication'.format(**global_vars)
    # try_and_print(message='Pidgin.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Pidgin.exe', source_url='https://ninite.com/pidgin/ninite.exe')
    # try_and_print(message='Skype.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Skype.exe', source_url='https://ninite.com/skype/ninite.exe')
    # try_and_print(message='Trillian.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Trillian.exe', source_url='https://ninite.com/trillian/ninite.exe')

    # # Ninite - Compression
    # print_success(' '*4 + 'Compression')
    # _path = r'{BaseDir}\Installers\Extras\Compression'.format(**global_vars)
    # try_and_print(message='7-Zip.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='7-Zip.exe', source_url='https://ninite.com/7zip/ninite.exe')
    # try_and_print(message='PeaZip.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PeaZip.exe', source_url='https://ninite.com/peazip/ninite.exe')
    # try_and_print(message='WinRAR.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinRAR.exe', source_url='https://ninite.com/winrar/ninite.exe')

    # # Ninite - Developer
    # print_success(' '*4 + 'Developer')
    # _path = r'{BaseDir}\Installers\Extras\Developer'.format(**global_vars)
    # try_and_print(message='Eclipse.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Eclipse.exe', source_url='https://ninite.com/eclipse/ninite.exe')
    # try_and_print(message='FileZilla.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='FileZilla.exe', source_url='https://ninite.com/filezilla/ninite.exe')
    # try_and_print(message='JDK 8.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='JDK 8.exe', source_url='https://ninite.com/jdk8/ninite.exe')
    # try_and_print(message='JDK 8 (x64).exe', function=download_file, other_results=other_results, out_dir=_path, out_name='JDK 8 (x64).exe', source_url='https://ninite.com/jdkx8/ninite.exe')
    # try_and_print(message='Notepad++.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Notepad++.exe', source_url='https://ninite.com/notepadplusplus/ninite.exe')
    # try_and_print(message='PuTTY.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PuTTY.exe', source_url='https://ninite.com/putty/ninite.exe')
    # try_and_print(message='Python 2.7.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Python 2.exe', source_url='https://ninite.com/python/ninite.exe')
    # try_and_print(message='Visual Studio Code.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Visual Studio Code.exe', source_url='https://ninite.com/vscode/ninite.exe')
    # try_and_print(message='WinMerge.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinMerge.exe', source_url='https://ninite.com/winmerge/ninite.exe')
    # try_and_print(message='WinSCP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinSCP.exe', source_url='https://ninite.com/winscp/ninite.exe')

    # # Ninite - File Sharing
    # print_success(' '*4 + 'File Sharing')
    # _path = r'{BaseDir}\Installers\Extras\File Sharing'.format(**global_vars)
    # try_and_print(message='qBittorrent.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='qBittorrent.exe', source_url='https://ninite.com/qbittorrent/ninite.exe')

    # # Ninite - Image-Photo
    # print_success(' '*4 + 'Image-Photo')
    # _path = r'{BaseDir}\Installers\Extras\Image-Photo'.format(**global_vars)
    # try_and_print(message='Blender.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Blender.exe', source_url='https://ninite.com/blender/ninite.exe')
    # try_and_print(message='FastStone.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='FastStone.exe', source_url='https://ninite.com/faststone/ninite.exe')
    # try_and_print(message='GIMP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='GIMP.exe', source_url='https://ninite.com/gimp/ninite.exe')
    # try_and_print(message='Greenshot.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Greenshot.exe', source_url='https://ninite.com/greenshot/ninite.exe')
    # try_and_print(message='Inkscape.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Inkscape.exe', source_url='https://ninite.com/inkscape/ninite.exe')
    # try_and_print(message='IrfanView.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='IrfanView.exe', source_url='https://ninite.com/irfanview/ninite.exe')
    # try_and_print(message='Krita.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Krita.exe', source_url='https://ninite.com/krita/ninite.exe')
    # try_and_print(message='Paint.NET.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Paint.NET.exe', source_url='https://ninite.com/paint.net/ninite.exe')
    # try_and_print(message='ShareX.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='ShareX.exe', source_url='https://ninite.com/sharex/ninite.exe')
    # try_and_print(message='XnView.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='XnView.exe', source_url='https://ninite.com/xnview/ninite.exe')

    # # Ninite - Misc
    # print_success(' '*4 + 'Misc')
    # _path = r'{BaseDir}\Installers\Extras\Misc'.format(**global_vars)
    # try_and_print(message='Evernote.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Evernote.exe', source_url='https://ninite.com/evernote/ninite.exe')
    # try_and_print(message='Everything.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Everything.exe', source_url='https://ninite.com/everything/ninite.exe')
    # try_and_print(message='KeePass 2.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='KeePass 2.exe', source_url='https://ninite.com/keepass2/ninite.exe')
    # try_and_print(message='Google Earth.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Earth.exe', source_url='https://ninite.com/googleearth/ninite.exe')
    # try_and_print(message='NV Access.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='NV Access.exe', source_url='https://ninite.com/nvda/ninite.exe')
    # try_and_print(message='Steam.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Steam.exe', source_url='https://ninite.com/steam/ninite.exe')

    # # Ninite - Office
    # print_success(' '*4 + 'Office')
    # _path = r'{BaseDir}\Installers\Extras\Office'.format(**global_vars)
    # try_and_print(message='CutePDF.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CutePDF.exe', source_url='https://ninite.com/cutepdf/ninite.exe')
    # try_and_print(message='Foxit Reader.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Foxit Reader.exe', source_url='https://ninite.com/foxit/ninite.exe')
    # try_and_print(message='LibreOffice.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='LibreOffice.exe', source_url='https://ninite.com/libreoffice/ninite.exe')
    # try_and_print(message='OpenOffice.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='OpenOffice.exe', source_url='https://ninite.com/openoffice/ninite.exe')
    # try_and_print(message='PDFCreator.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PDFCreator.exe', source_url='https://ninite.com/pdfcreator/ninite.exe')
    # try_and_print(message='SumatraPDF.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SumatraPDF.exe', source_url='https://ninite.com/sumatrapdf/ninite.exe')
    # try_and_print(message='Thunderbird.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Thunderbird.exe', source_url='https://ninite.com/thunderbird/ninite.exe')

    # # Ninite - Runtimes
    # print_success(' '*4 + 'Runtimes')
    # _path = r'{BaseDir}\Installers\Extras\Runtimes'.format(**global_vars)
    # try_and_print(message='Adobe Air.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Adobe Air.exe', source_url='https://ninite.com/air/ninite.exe')
    # try_and_print(message='dotNET.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='dotNET.exe', source_url='https://ninite.com/.net4.7/ninite.exe')
    # try_and_print(message='Java 8.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Java 8.exe', source_url='https://ninite.com/java8/ninite.exe')
    # try_and_print(message='Shockwave.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Shockwave.exe', source_url='https://ninite.com/shockwave/ninite.exe')
    # try_and_print(message='Silverlight.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Silverlight.exe', source_url='https://ninite.com/silverlight/ninite.exe')

    # # Ninite - Security
    # print_success(' '*4 + 'Security')
    # _path = r'{BaseDir}\Installers\Extras\Security'.format(**global_vars)
    # try_and_print(message='Avast.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Avast.exe', source_url='https://ninite.com/avast/ninite.exe')
    # try_and_print(message='AVG.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='AVG.exe', source_url='https://ninite.com/avg/ninite.exe')
    # try_and_print(message='Avira.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Avira.exe', source_url='https://ninite.com/avira/ninite.exe')
    # try_and_print(message='Microsoft Security Essentials.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Microsoft Security Essentials.exe', source_url='https://ninite.com/essentials/ninite.exe')
    # try_and_print(message='Malwarebytes Anti-Malware.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Malwarebytes Anti-Malware.exe', source_url='https://ninite.com/malwarebytes/ninite.exe')
    # try_and_print(message='Spybot 2.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Spybot 2.exe', source_url='https://ninite.com/spybot2/ninite.exe')
    # try_and_print(message='SUPERAntiSpyware.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SUPERAntiSpyware.exe', source_url='https://ninite.com/super/ninite.exe')

    # # Ninite - Utilities
    # print_success(' '*4 + 'Utilities')
    # _path = r'{BaseDir}\Installers\Extras\Utilities'.format(**global_vars)
    # try_and_print(message='CDBurnerXP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CDBurnerXP.exe', source_url='https://ninite.com/cdburnerxp/ninite.exe')
    # try_and_print(message='Classic Start.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Classic Start.exe', source_url='https://ninite.com/classicstart/ninite.exe')
    # try_and_print(message='Glary Utilities.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Glary Utilities.exe', source_url='https://ninite.com/glary/ninite.exe')
    # try_and_print(message='ImgBurn.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='ImgBurn.exe', source_url='https://ninite.com/imgburn/ninite.exe')
    # try_and_print(message='InfraRecorder.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='InfraRecorder.exe', source_url='https://ninite.com/infrarecorder/ninite.exe')
    # try_and_print(message='Launchy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Launchy.exe', source_url='https://ninite.com/launchy/ninite.exe')
    # try_and_print(message='RealVNC.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='RealVNC.exe', source_url='https://ninite.com/realvnc/ninite.exe')
    # try_and_print(message='Revo Uninstaller.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Revo Uninstaller.exe', source_url='https://ninite.com/revo/ninite.exe')
    # try_and_print(message='TeamViewer 12.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='TeamViewer 12.exe', source_url='https://ninite.com/teamviewer12/ninite.exe')
    # try_and_print(message='TeraCopy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='TeraCopy.exe', source_url='https://ninite.com/teracopy/ninite.exe')
    # try_and_print(message='WinDirStat.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinDirStat.exe', source_url='https://ninite.com/windirstat/ninite.exe')

    # # Ninite - Web Browsers
    # print_success(' '*4 + 'Web Browsers')
    # _path = r'{BaseDir}\Installers\Extras\Web Browsers'.format(**global_vars)
    # try_and_print(message='Google Chrome.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Chrome.exe', source_url='https://ninite.com/chrome/ninite.exe')
    # try_and_print(message='Mozilla Firefox.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Mozilla Firefox.exe', source_url='https://ninite.com/firefox/ninite.exe')
    # try_and_print(message='Opera Chromium.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Opera Chromium.exe', source_url='https://ninite.com/operaChromium/ninite.exe')
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
    extract_to_cbin('npp.7z', 'NotepadPlusPlus')
    
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
