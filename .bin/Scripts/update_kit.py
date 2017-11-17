# Wizard Kit: Download the latest versions of the programs in the kit

import os
import re

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Kit Update Tool')
from functions import *
vars = init_vars()
vars_os = init_vars_os()
curl = '{BinDir}/curl/curl.exe'.format(**vars)
seven_zip = '{BinDir}/7-Zip/7za.exe'.format(**vars)
if vars_os['Arch'] == 64:
    seven_zip = seven_zip.replace('7za', '7za64')

def download_file(out_dir, out_name, source_url):
    """Downloads a file using curl."""
    print('Downloading: {out_name}'.format(out_name=out_name))
    _args = [
        '-#LSfo',
        '{out_dir}/{out_name}'.format(out_dir=out_dir, out_name=out_name),
        source_url
    ]
    try:
        os.makedirs(out_dir, exist_ok=True)
        run_program(curl, _args, pipe=False)
    except:
        print_error('Falied to download file.')

def resolve_dynamic_url(source_url, regex):
    """Download the "download page" and scan for a url using the regex provided; returns str."""
    # Download the file
    _tmp_file = '{TmpDir}/webpage.tmp'.format(**vars)
    _args = ['-#LSfo', _tmp_file, source_url]
    try:
        os.makedirs(vars['TmpDir'], exist_ok=True)
        run_program(curl, _args)
    except:
        print_error('Falied to resolve dynamic url')
    
    # Scan the file for the regex
    with open(_tmp_file, 'r') as file:
        for line in file:
            if re.search(regex, line):
                _url = line.strip()
                _url = re.sub(r'.*(a |)href="([^"]+)".*', r'\2', _url)
                _url = re.sub(r".*(a |)href='([^']+)'.*", r'\2', _url)
                break
    
    # Cleanup and return
    os.remove(_tmp_file)
    return _url

if __name__ == '__main__':
    stay_awake(vars_wk)
    ## Diagnostics ##
    # HitmanPro
    _path = '{BinDir}/HitmanPro'.format(**vars)
    _name = 'HitmanPro.exe'
    _url = 'http://dl.surfright.nl/HitmanPro.exe'
    download_file(_path, _name, _url)
    _name = 'HitmanPro64.exe'
    _url = 'http://dl.surfright.nl/HitmanPro_x64.exe'
    download_file(_path, _name, _url)

    ## VR-OSR ##
    # AdwCleaner
    _path = vars['BinDir']
    _name = 'AdwCleaner.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/adwcleaner/dl/125/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/a/adwcleaner/AdwCleaner\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

    # ESET Online Scanner
    _path = vars['BinDir']
    _name = 'ESET.exe'
    _url = 'http://download.eset.com/special/eos/esetsmartinstaller_enu.exe'
    download_file(_path, _name, _url)

    # Junkware Removal Tool
    _path = vars['BinDir']
    _name = 'JRT.exe'
    _url = 'http://downloads.malwarebytes.org/file/jrt'
    download_file(_path, _name, _url)

    # Kaspersky Virus Removal Tool
    _path = vars['BinDir']
    _name = 'KVRT.exe'
    _url = 'http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe'
    download_file(_path, _name, _url)

    # RKill
    _path = '{BinDir}/RKill'.format(**vars)
    _name = 'RKill.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/rkill/dl/10/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/r/rkill/rkill\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

    # TDSSKiller
    _path = vars['BinDir']
    _name = 'TDSSKiller.exe'
    _url = 'http://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe'
    download_file(_path, _name, _url)

    ## Driver Tools ##
    # Intel Driver Update Utility
    _path = '{BinDir}/_Drivers'.format(**vars)
    _name = 'Intel Driver Update Utility.exe'
    _dl_page = 'http://www.intel.com/content/www/us/en/support/detect.html'
    _regex = r'a href.*http(s|)://downloadmirror\.intel\.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+/Intel%20Driver%20Update%20Utility%20Installer.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

    # Intel SSD Toolbox
    _path = '{BinDir}/_Drivers'.format(**vars)
    _name = 'Intel SSD Toolbox.exe'
    _dl_page = 'https://downloadcenter.intel.com/download/26085/Intel-Solid-State-Drive-Toolbox'
    _regex = r'href=./downloads/eula/[0-9]+/Intel-Solid-State-Drive-Toolbox.httpDown=https\%3A\%2F\%2Fdownloadmirror\.intel\.com\%2F[0-9]+\%2Feng\%2FIntel\%20SSD\%20Toolbox\%20-\%20v[0-9\.]+.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = re.sub(r'.*httpDown=(.*)', r'\1', _url, flags=re.IGNORECASE)
    _url = _url.replace('%3A', ':')
    _url = _url.replace('%2F', '/')
    download_file(_path, _name, _url)

    #~Broken~# # Samsung Magician
    print_warning('Samsung Magician section is broken.')
    print('Please manually put "Samsung Magician.exe" into "{BinDir}\\_Drivers\\"')
    #~Broken~# _path = '{BinDir}/_Drivers'.format(**vars)
    #~Broken~# _name = 'Samsung Magician.zip'
    #~Broken~# _dl_page = 'http://www.samsung.com/semiconductor/minisite/ssd/download/tools.html'
    #~Broken~# _regex = r'href=./semiconductor/minisite/ssd/downloads/software/Samsung_Magician_Setup_v[0-9]+.zip'
    #~Broken~# _url = resolve_dynamic_url(_dl_page, _regex)
    #~Broken~# # Convert relative url to absolute
    #~Broken~# _url = 'http://www.samsung.com' + _url
    #~Broken~# download_file(_path, _name, _url)
    #~Broken~# # Extract and replace old copy
    #~Broken~# _args = [
    #~Broken~#     'e', '"{BinDir}/_Drivers/Samsung Magician.zip"'.format(**vars),
    #~Broken~#     '-aoa', '-bso0', '-bsp0',
    #~Broken~#     '-o"{BinDir}/_Drivers"'.format(**vars)
    #~Broken~# ]
    #~Broken~# run_program(seven_zip, _args)
    #~Broken~# try:
    #~Broken~#     os.remove('{BinDir}/_Drivers/Samsung Magician.zip'.format(**vars))
    #~Broken~#     #~PoSH~# Move-Item "$bin\_Drivers\Samsung*exe" "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null
    #~Broken~# except:
    #~Broken~#     pass

    # SanDisk Express Cache
    _path = '{BinDir}/_Drivers'.format(**vars)
    _name = 'SanDisk Express Cache.exe'
    _url = 'http://mp3support.sandisk.com/ReadyCache/ExpressCacheSetup.exe'
    download_file(_path, _name, _url)

    ## Installers ##
    # Ninite - Bundles
    _path = '{BaseDir}/Installers/Extras/Bundles'.format(**vars)
    download_file(_path, 'Runtimes.exe', 'https://ninite.com/.net4.6.2-air-java8-silverlight/ninite.exe')
    download_file(_path, 'Legacy.exe', 'https://ninite.com/.net4.6.2-7zip-air-chrome-firefox-java8-silverlight-vlc/ninite.exe')
    download_file(_path, 'Modern.exe', 'https://ninite.com/.net4.6.2-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc/ninite.exe')

    # Ninite - Audio-Video
    _path = '{BaseDir}/Installers/Extras/Audio-Video'.format(**vars)
    download_file(_path, 'AIMP.exe', 'https://ninite.com/aimp/ninite.exe')
    download_file(_path, 'Audacity.exe', 'https://ninite.com/audacity/ninite.exe')
    download_file(_path, 'CCCP.exe', 'https://ninite.com/cccp/ninite.exe')
    download_file(_path, 'Foobar2000.exe', 'https://ninite.com/foobar/ninite.exe')
    download_file(_path, 'GOM.exe', 'https://ninite.com/gom/ninite.exe')
    download_file(_path, 'iTunes.exe', 'https://ninite.com/itunes/ninite.exe')
    download_file(_path, 'K-Lite Codecs.exe', 'https://ninite.com/klitecodecs/ninite.exe')
    download_file(_path, 'KMPlayer.exe', 'https://ninite.com/kmplayer/ninite.exe')
    download_file(_path, 'MediaMonkey.exe', 'https://ninite.com/mediamonkey/ninite.exe')
    download_file(_path, 'MusicBee.exe', 'https://ninite.com/musicbee/ninite.exe')
    download_file(_path, 'Spotify.exe', 'https://ninite.com/spotify/ninite.exe')
    download_file(_path, 'VLC.exe', 'https://ninite.com/vlc/ninite.exe')
    download_file(_path, 'Winamp.exe', 'https://ninite.com/winamp/ninite.exe')

    # Ninite - Cloud Storage
    _path = '{BaseDir}/Installers/Extras/Cloud Storage'.format(**vars)
    download_file(_path, 'BitTorrent Sync.exe', 'https://ninite.com/bittorrentsync/ninite.exe')
    download_file(_path, 'Dropbox.exe', 'https://ninite.com/dropbox/ninite.exe')
    download_file(_path, 'Google Drive.exe', 'https://ninite.com/googledrive/ninite.exe')
    download_file(_path, 'Mozy.exe', 'https://ninite.com/mozy/ninite.exe')
    download_file(_path, 'OneDrive.exe', 'https://ninite.com/onedrive/ninite.exe')
    download_file(_path, 'SugarSync.exe', 'https://ninite.com/sugarsync/ninite.exe')

    # Ninite - Communication
    _path = '{BaseDir}/Installers/Extras/Communication'.format(**vars)
    download_file(_path, 'AIM.exe', 'https://ninite.com/aim/ninite.exe')
    download_file(_path, 'Pidgin.exe', 'https://ninite.com/pidgin/ninite.exe')
    download_file(_path, 'Skype.exe', 'https://ninite.com/skype/ninite.exe')
    download_file(_path, 'Trillian.exe', 'https://ninite.com/trillian/ninite.exe')

    # Ninite - Compression
    _path = '{BaseDir}/Installers/Extras/Compression'.format(**vars)
    download_file(_path, '7-Zip.exe', 'https://ninite.com/7zip/ninite.exe')
    download_file(_path, 'PeaZip.exe', 'https://ninite.com/peazip/ninite.exe')
    download_file(_path, 'WinRAR.exe', 'https://ninite.com/winrar/ninite.exe')

    # Ninite - Developer
    _path = '{BaseDir}/Installers/Extras/Developer'.format(**vars)
    download_file(_path, 'Eclipse.exe', 'https://ninite.com/eclipse/ninite.exe')
    download_file(_path, 'FileZilla.exe', 'https://ninite.com/filezilla/ninite.exe')
    download_file(_path, 'JDK 8.exe', 'https://ninite.com/jdk8/ninite.exe')
    download_file(_path, 'JDK 8 (x64).exe', 'https://ninite.com/jdkx8/ninite.exe')
    download_file(_path, 'Notepad++.exe', 'https://ninite.com/notepadplusplus/ninite.exe')
    download_file(_path, 'PuTTY.exe', 'https://ninite.com/putty/ninite.exe')
    download_file(_path, 'Python 2.exe', 'https://ninite.com/python/ninite.exe')
    download_file(_path, 'Visual Studio Code.exe', 'https://ninite.com/vscode/ninite.exe')
    download_file(_path, 'WinMerge.exe', 'https://ninite.com/winmerge/ninite.exe')
    download_file(_path, 'WinSCP.exe', 'https://ninite.com/winscp/ninite.exe')

    # Ninite - File Sharing
    _path = '{BaseDir}/Installers/Extras/File Sharing'.format(**vars)
    download_file(_path, 'eMule.exe', 'https://ninite.com/emule/ninite.exe')
    download_file(_path, 'qBittorrent.exe', 'https://ninite.com/qbittorrent/ninite.exe')

    # Ninite - Image-Photo
    _path = '{BaseDir}/Installers/Extras/Image-Photo'.format(**vars)
    download_file(_path, 'FastStone.exe', 'https://ninite.com/faststone/ninite.exe')
    download_file(_path, 'GIMP.exe', 'https://ninite.com/gimp/ninite.exe')
    download_file(_path, 'Greenshot.exe', 'https://ninite.com/greenshot/ninite.exe')
    download_file(_path, 'Inkscape.exe', 'https://ninite.com/inkscape/ninite.exe')
    download_file(_path, 'IrfanView.exe', 'https://ninite.com/irfanview/ninite.exe')
    download_file(_path, 'Paint.NET.exe', 'https://ninite.com/paint.net/ninite.exe')
    download_file(_path, 'ShareX.exe', 'https://ninite.com/sharex/ninite.exe')
    download_file(_path, 'XnView.exe', 'https://ninite.com/xnview/ninite.exe')

    # Ninite - Misc
    _path = '{BaseDir}/Installers/Extras/Misc'.format(**vars)
    download_file(_path, 'Classic Start.exe', 'https://ninite.com/classicstart/ninite.exe')
    download_file(_path, 'Evernote.exe', 'https://ninite.com/evernote/ninite.exe')
    download_file(_path, 'Everything.exe', 'https://ninite.com/everything/ninite.exe')
    download_file(_path, 'Google Earth.exe', 'https://ninite.com/googleearth/ninite.exe')
    download_file(_path, 'NV Access.exe', 'https://ninite.com/nvda/ninite.exe')
    download_file(_path, 'Steam.exe', 'https://ninite.com/steam/ninite.exe')

    # Ninite - Office
    _path = '{BaseDir}/Installers/Extras/Office'.format(**vars)
    download_file(_path, 'CutePDF.exe', 'https://ninite.com/cutepdf/ninite.exe')
    download_file(_path, 'Foxit Reader.exe', 'https://ninite.com/foxit/ninite.exe')
    download_file(_path, 'LibreOffice.exe', 'https://ninite.com/libreoffice/ninite.exe')
    download_file(_path, 'OpenOffice.exe', 'https://ninite.com/openoffice/ninite.exe')
    download_file(_path, 'PDFCreator.exe', 'https://ninite.com/pdfcreator/ninite.exe')
    download_file(_path, 'SumatraPDF.exe', 'https://ninite.com/sumatrapdf/ninite.exe')
    download_file(_path, 'Thunderbird.exe', 'https://ninite.com/thunderbird/ninite.exe')

    # Ninite - Runtimes
    _path = '{BaseDir}/Installers/Extras/Runtimes'.format(**vars)
    download_file(_path, 'Adobe Air.exe', 'https://ninite.com/air/ninite.exe')
    download_file(_path, 'dotNET.exe', 'https://ninite.com/.net4.6.2/ninite.exe')
    download_file(_path, 'Java 8.exe', 'https://ninite.com/java8/ninite.exe')
    download_file(_path, 'Shockwave.exe', 'https://ninite.com/shockwave/ninite.exe')
    download_file(_path, 'Silverlight.exe', 'https://ninite.com/silverlight/ninite.exe')

    # Ninite - Security
    _path = '{BaseDir}/Installers/Extras/Security'.format(**vars)
    download_file(_path, 'Ad-Aware.exe', 'https://ninite.com/adaware/ninite.exe')
    download_file(_path, 'Avast.exe', 'https://ninite.com/avast/ninite.exe')
    download_file(_path, 'AVG.exe', 'https://ninite.com/avg/ninite.exe')
    download_file(_path, 'Avira.exe', 'https://ninite.com/avira/ninite.exe')
    download_file(_path, 'Microsoft Security Essentials.exe', 'https://ninite.com/essentials/ninite.exe')
    download_file(_path, 'Malwarebytes Anti-Malware.exe', 'https://ninite.com/malwarebytes/ninite.exe')
    download_file(_path, 'Spybot 2.exe', 'https://ninite.com/spybot2/ninite.exe')
    download_file(_path, 'SUPERAntiSpyware.exe', 'https://ninite.com/super/ninite.exe')

    # Ninite - Utilities
    _path = '{BaseDir}/Installers/Extras/Utilities'.format(**vars)
    download_file(_path, 'Auslogics DiskDefrag.exe', 'https://ninite.com/auslogics/ninite.exe')
    download_file(_path, 'CDBurnerXP.exe', 'https://ninite.com/cdburnerxp/ninite.exe')
    download_file(_path, 'Glary Utilities.exe', 'https://ninite.com/glary/ninite.exe')
    download_file(_path, 'ImgBurn.exe', 'https://ninite.com/imgburn/ninite.exe')
    download_file(_path, 'InfraRecorder.exe', 'https://ninite.com/infrarecorder/ninite.exe')
    download_file(_path, 'KeePass 2.exe', 'https://ninite.com/keepass2/ninite.exe')
    download_file(_path, 'Launchy.exe', 'https://ninite.com/launchy/ninite.exe')
    download_file(_path, 'RealVNC.exe', 'https://ninite.com/realvnc/ninite.exe')
    download_file(_path, 'Revo Uninstaller.exe', 'https://ninite.com/revo/ninite.exe')
    download_file(_path, 'TeamViewer 11.exe', 'https://ninite.com/teamviewer11/ninite.exe')
    download_file(_path, 'TeraCopy.exe', 'https://ninite.com/teracopy/ninite.exe')
    download_file(_path, 'WinDirStat.exe', 'https://ninite.com/windirstat/ninite.exe')

    # Ninite - Web Browsers
    _path = '{BaseDir}/Installers/Extras/Web Browsers'.format(**vars)
    download_file(_path, 'Google Chrome.exe', 'https://ninite.com/chrome/ninite.exe')
    download_file(_path, 'Mozilla Firefox.exe', 'https://ninite.com/firefox/ninite.exe')
    download_file(_path, 'Opera Chromium.exe', 'https://ninite.com/operaChromium/ninite.exe')
    
    ## Misc ##
    # Sysinternals
    _path = '{BinDir}/tmp'.format(**vars)
    _name = 'SysinternalsSuite.zip'
    _url = 'https://download.sysinternals.com/files/SysinternalsSuite.zip'
    download_file(_path, _name, _url)
    # Extract
    _args = [
        'e', '"{BinDir}/tmp/SysinternalsSuite.zip"'.format(**vars),
        '-aoa', '-bso0', '-bsp0',
        '-o"{BinDir}/SysinternalsSuite"'.format(**vars)]
    run_program(seven_zip, _args)
    try:
        os.remove('{BinDir}/tmp/SysinternalsSuite.zip'.format(**vars))
    except:
        pass

    pause("Press Enter to exit...")
    kill_process('caffeine.exe')
    quit()
