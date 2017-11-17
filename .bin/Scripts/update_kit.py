# Wizard Kit: Download the latest versions of the programs in the kit

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.build import *
init_global_vars()
os.system('title {}: Kit Update Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
    try:
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            }}
        stay_awake()
        
        # Diagnostics
        # print_info('Diagnostics')
        # try_and_print(message='HitmanPro...', function=update_hitmanpro, other_results=other_results)
        
        # VR/OSR
        # print_info('VR/OSR')
        # try_and_print(message='AdwCleaner...', function=update_adwcleaner, other_results=other_results)
        # try_and_print(message='ESET...', function=update_eset, other_results=other_results)
        # try_and_print(message='JRT...', function=update_jrt, other_results=other_results)
        # try_and_print(message='KVRT...', function=update_kvrt, other_results=other_results)
        # try_and_print(message='RKill...', function=update_rkill, other_results=other_results)
        # try_and_print(message='TDSSKiller...', function=update_tdsskiller, other_results=other_results)
        
        # Driver Tools
        print_info('Driver Tools')
        # try_and_print(message='Intel Driver Update Utility...', function=update_intel_driver_utility, other_results=other_results)
        # try_and_print(message='Intel SSD Toolbox...', function=update_intel_ssd_toolbox, other_results=other_results)
        # try_and_print(message='Samsung Magician...', function=update_samsung_magician, other_results=other_results)
        try_and_print(message='Samsung Magician...', function=update_samsung_magician, silent_function=False)
        
        # Ninite - Bundles
        print_info('Installers')
        print_success(' '*4 + 'Ninite Bundles')
        _path = r'{BaseDir}\Installers\Extras\Bundles'.format(**global_vars)
        try_and_print(message='Runtimes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Runtimes.exe', source_url='https://ninite.com/.net4.7-air-java8-silverlight/ninite.exe')
        try_and_print(message='Legacy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Legacy.exe', source_url='https://ninite.com/.net4.7-7zip-air-chrome-firefox-java8-silverlight-vlc/ninite.exe')
        try_and_print(message='Modern.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Modern.exe', source_url='https://ninite.com/.net4.7-7zip-air-chrome-classicstart-firefox-java8-silverlight-vlc/ninite.exe')
            
        # Ninite - Audio-Video
        print_success(' '*4 + 'Audio-Video')
        _path = r'{BaseDir}\Installers\Extras\Audio-Video'.format(**global_vars)
        try_and_print(message='AIMP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='AIMP.exe', source_url='https://ninite.com/aimp/ninite.exe')
        try_and_print(message='Audacity.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Audacity.exe', source_url='https://ninite.com/audacity/ninite.exe')
        try_and_print(message='CCCP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CCCP.exe', source_url='https://ninite.com/cccp/ninite.exe')
        try_and_print(message='Foobar2000.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Foobar2000.exe', source_url='https://ninite.com/foobar/ninite.exe')
        try_and_print(message='GOM.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='GOM.exe', source_url='https://ninite.com/gom/ninite.exe')
        try_and_print(message='iTunes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='HandBrake.exe', source_url='https://ninite.com/handbrake/ninite.exe')
        try_and_print(message='iTunes.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='iTunes.exe', source_url='https://ninite.com/itunes/ninite.exe')
        try_and_print(message='K-Lite Codecs.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='K-Lite Codecs.exe', source_url='https://ninite.com/klitecodecs/ninite.exe')
        try_and_print(message='MediaMonkey.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='MediaMonkey.exe', source_url='https://ninite.com/mediamonkey/ninite.exe')
        try_and_print(message='MusicBee.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='MusicBee.exe', source_url='https://ninite.com/musicbee/ninite.exe')
        try_and_print(message='Spotify.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Spotify.exe', source_url='https://ninite.com/spotify/ninite.exe')
        try_and_print(message='VLC.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='VLC.exe', source_url='https://ninite.com/vlc/ninite.exe')
        try_and_print(message='Winamp.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Winamp.exe', source_url='https://ninite.com/winamp/ninite.exe')

        # Ninite - Cloud Storage
        print_success(' '*4 + 'Cloud Storage')
        _path = r'{BaseDir}\Installers\Extras\Cloud Storage'.format(**global_vars)
        try_and_print(message='Dropbox.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Dropbox.exe', source_url='https://ninite.com/dropbox/ninite.exe')
        try_and_print(message='Google Backup & Sync.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Backup & Sync.exe', source_url='https://ninite.com/googlebackupandsync/ninite.exe')
        try_and_print(message='Mozy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Mozy.exe', source_url='https://ninite.com/mozy/ninite.exe')
        try_and_print(message='OneDrive.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='OneDrive.exe', source_url='https://ninite.com/onedrive/ninite.exe')
        try_and_print(message='SugarSync.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SugarSync.exe', source_url='https://ninite.com/sugarsync/ninite.exe')

        # Ninite - Communication
        print_success(' '*4 + 'Communication')
        _path = r'{BaseDir}\Installers\Extras\Communication'.format(**global_vars)
        try_and_print(message='Pidgin.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Pidgin.exe', source_url='https://ninite.com/pidgin/ninite.exe')
        try_and_print(message='Skype.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Skype.exe', source_url='https://ninite.com/skype/ninite.exe')
        try_and_print(message='Trillian.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Trillian.exe', source_url='https://ninite.com/trillian/ninite.exe')

        # Ninite - Compression
        print_success(' '*4 + 'Compression')
        _path = r'{BaseDir}\Installers\Extras\Compression'.format(**global_vars)
        try_and_print(message='7-Zip.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='7-Zip.exe', source_url='https://ninite.com/7zip/ninite.exe')
        try_and_print(message='PeaZip.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PeaZip.exe', source_url='https://ninite.com/peazip/ninite.exe')
        try_and_print(message='WinRAR.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinRAR.exe', source_url='https://ninite.com/winrar/ninite.exe')

        # Ninite - Developer
        print_success(' '*4 + 'Developer')
        _path = r'{BaseDir}\Installers\Extras\Developer'.format(**global_vars)
        try_and_print(message='Eclipse.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Eclipse.exe', source_url='https://ninite.com/eclipse/ninite.exe')
        try_and_print(message='FileZilla.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='FileZilla.exe', source_url='https://ninite.com/filezilla/ninite.exe')
        try_and_print(message='JDK 8.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='JDK 8.exe', source_url='https://ninite.com/jdk8/ninite.exe')
        try_and_print(message='JDK 8 (x64).exe', function=download_file, other_results=other_results, out_dir=_path, out_name='JDK 8 (x64).exe', source_url='https://ninite.com/jdkx8/ninite.exe')
        try_and_print(message='Notepad++.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Notepad++.exe', source_url='https://ninite.com/notepadplusplus/ninite.exe')
        try_and_print(message='PuTTY.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PuTTY.exe', source_url='https://ninite.com/putty/ninite.exe')
        try_and_print(message='Python 2.7.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Python 2.exe', source_url='https://ninite.com/python/ninite.exe')
        try_and_print(message='Visual Studio Code.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Visual Studio Code.exe', source_url='https://ninite.com/vscode/ninite.exe')
        try_and_print(message='WinMerge.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinMerge.exe', source_url='https://ninite.com/winmerge/ninite.exe')
        try_and_print(message='WinSCP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinSCP.exe', source_url='https://ninite.com/winscp/ninite.exe')

        # Ninite - File Sharing
        print_success(' '*4 + 'File Sharing')
        _path = r'{BaseDir}\Installers\Extras\File Sharing'.format(**global_vars)
        try_and_print(message='qBittorrent.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='qBittorrent.exe', source_url='https://ninite.com/qbittorrent/ninite.exe')

        # Ninite - Image-Photo
        print_success(' '*4 + 'Image-Photo')
        _path = r'{BaseDir}\Installers\Extras\Image-Photo'.format(**global_vars)
        try_and_print(message='Blender.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Blender.exe', source_url='https://ninite.com/blender/ninite.exe')
        try_and_print(message='FastStone.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='FastStone.exe', source_url='https://ninite.com/faststone/ninite.exe')
        try_and_print(message='GIMP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='GIMP.exe', source_url='https://ninite.com/gimp/ninite.exe')
        try_and_print(message='Greenshot.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Greenshot.exe', source_url='https://ninite.com/greenshot/ninite.exe')
        try_and_print(message='Inkscape.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Inkscape.exe', source_url='https://ninite.com/inkscape/ninite.exe')
        try_and_print(message='IrfanView.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='IrfanView.exe', source_url='https://ninite.com/irfanview/ninite.exe')
        try_and_print(message='Krita.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Krita.exe', source_url='https://ninite.com/krita/ninite.exe')
        try_and_print(message='Paint.NET.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Paint.NET.exe', source_url='https://ninite.com/paint.net/ninite.exe')
        try_and_print(message='ShareX.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='ShareX.exe', source_url='https://ninite.com/sharex/ninite.exe')
        try_and_print(message='XnView.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='XnView.exe', source_url='https://ninite.com/xnview/ninite.exe')

        # Ninite - Misc
        print_success(' '*4 + 'Misc')
        _path = r'{BaseDir}\Installers\Extras\Misc'.format(**global_vars)
        try_and_print(message='Evernote.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Evernote.exe', source_url='https://ninite.com/evernote/ninite.exe')
        try_and_print(message='Everything.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Everything.exe', source_url='https://ninite.com/everything/ninite.exe')
        try_and_print(message='KeePass 2.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='KeePass 2.exe', source_url='https://ninite.com/keepass2/ninite.exe')
        try_and_print(message='Google Earth.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Earth.exe', source_url='https://ninite.com/googleearth/ninite.exe')
        try_and_print(message='NV Access.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='NV Access.exe', source_url='https://ninite.com/nvda/ninite.exe')
        try_and_print(message='Steam.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Steam.exe', source_url='https://ninite.com/steam/ninite.exe')

        # Ninite - Office
        print_success(' '*4 + 'Office')
        _path = r'{BaseDir}\Installers\Extras\Office'.format(**global_vars)
        try_and_print(message='CutePDF.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CutePDF.exe', source_url='https://ninite.com/cutepdf/ninite.exe')
        try_and_print(message='Foxit Reader.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Foxit Reader.exe', source_url='https://ninite.com/foxit/ninite.exe')
        try_and_print(message='LibreOffice.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='LibreOffice.exe', source_url='https://ninite.com/libreoffice/ninite.exe')
        try_and_print(message='OpenOffice.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='OpenOffice.exe', source_url='https://ninite.com/openoffice/ninite.exe')
        try_and_print(message='PDFCreator.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='PDFCreator.exe', source_url='https://ninite.com/pdfcreator/ninite.exe')
        try_and_print(message='SumatraPDF.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SumatraPDF.exe', source_url='https://ninite.com/sumatrapdf/ninite.exe')
        try_and_print(message='Thunderbird.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Thunderbird.exe', source_url='https://ninite.com/thunderbird/ninite.exe')

        # Ninite - Runtimes
        print_success(' '*4 + 'Runtimes')
        _path = r'{BaseDir}\Installers\Extras\Runtimes'.format(**global_vars)
        try_and_print(message='Adobe Air.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Adobe Air.exe', source_url='https://ninite.com/air/ninite.exe')
        try_and_print(message='dotNET.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='dotNET.exe', source_url='https://ninite.com/.net4.7/ninite.exe')
        try_and_print(message='Java 8.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Java 8.exe', source_url='https://ninite.com/java8/ninite.exe')
        try_and_print(message='Shockwave.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Shockwave.exe', source_url='https://ninite.com/shockwave/ninite.exe')
        try_and_print(message='Silverlight.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Silverlight.exe', source_url='https://ninite.com/silverlight/ninite.exe')

        # Ninite - Security
        print_success(' '*4 + 'Security')
        _path = r'{BaseDir}\Installers\Extras\Security'.format(**global_vars)
        try_and_print(message='Avast.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Avast.exe', source_url='https://ninite.com/avast/ninite.exe')
        try_and_print(message='AVG.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='AVG.exe', source_url='https://ninite.com/avg/ninite.exe')
        try_and_print(message='Avira.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Avira.exe', source_url='https://ninite.com/avira/ninite.exe')
        try_and_print(message='Microsoft Security Essentials.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Microsoft Security Essentials.exe', source_url='https://ninite.com/essentials/ninite.exe')
        try_and_print(message='Malwarebytes Anti-Malware.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Malwarebytes Anti-Malware.exe', source_url='https://ninite.com/malwarebytes/ninite.exe')
        try_and_print(message='Spybot 2.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Spybot 2.exe', source_url='https://ninite.com/spybot2/ninite.exe')
        try_and_print(message='SUPERAntiSpyware.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='SUPERAntiSpyware.exe', source_url='https://ninite.com/super/ninite.exe')

        # Ninite - Utilities
        print_success(' '*4 + 'Utilities')
        _path = r'{BaseDir}\Installers\Extras\Utilities'.format(**global_vars)
        try_and_print(message='CDBurnerXP.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='CDBurnerXP.exe', source_url='https://ninite.com/cdburnerxp/ninite.exe')
        try_and_print(message='Classic Start.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Classic Start.exe', source_url='https://ninite.com/classicstart/ninite.exe')
        try_and_print(message='Glary Utilities.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Glary Utilities.exe', source_url='https://ninite.com/glary/ninite.exe')
        try_and_print(message='ImgBurn.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='ImgBurn.exe', source_url='https://ninite.com/imgburn/ninite.exe')
        try_and_print(message='InfraRecorder.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='InfraRecorder.exe', source_url='https://ninite.com/infrarecorder/ninite.exe')
        try_and_print(message='Launchy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Launchy.exe', source_url='https://ninite.com/launchy/ninite.exe')
        try_and_print(message='RealVNC.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='RealVNC.exe', source_url='https://ninite.com/realvnc/ninite.exe')
        try_and_print(message='Revo Uninstaller.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Revo Uninstaller.exe', source_url='https://ninite.com/revo/ninite.exe')
        try_and_print(message='TeamViewer 12.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='TeamViewer 12.exe', source_url='https://ninite.com/teamviewer12/ninite.exe')
        try_and_print(message='TeraCopy.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='TeraCopy.exe', source_url='https://ninite.com/teracopy/ninite.exe')
        try_and_print(message='WinDirStat.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='WinDirStat.exe', source_url='https://ninite.com/windirstat/ninite.exe')

        # Ninite - Web Browsers
        print_success(' '*4 + 'Web Browsers')
        _path = r'{BaseDir}\Installers\Extras\Web Browsers'.format(**global_vars)
        try_and_print(message='Google Chrome.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Google Chrome.exe', source_url='https://ninite.com/chrome/ninite.exe')
        try_and_print(message='Mozilla Firefox.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Mozilla Firefox.exe', source_url='https://ninite.com/firefox/ninite.exe')
        try_and_print(message='Opera Chromium.exe', function=download_file, other_results=other_results, out_dir=_path, out_name='Opera Chromium.exe', source_url='https://ninite.com/operaChromium/ninite.exe')
        
        # Misc
        # print_info('Misc')
        # try_and_print(message='SysinternalsSuite...', function=update_sysinternalssuite, other_results=other_results)
        
        # Done
        print_standard('\nDone.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
