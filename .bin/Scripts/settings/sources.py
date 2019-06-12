'''Wizard Kit: Settings - Sources'''
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2 tw=0

SOURCE_URLS = {
  'Adobe Reader DC': 'http://ardownload.adobe.com/pub/adobe/reader/win/AcrobatDC/1901020098/AcroRdrDC1901020098_en_US.exe',
  'AdwCleaner': 'https://downloads.malwarebytes.com/file/adwcleaner',
  'AIDA64': 'http://download.aida64.com/aida64engineer599.zip',
  'aria2': 'https://github.com/aria2/aria2/releases/download/release-1.34.0/aria2-1.34.0-win-32bit-build1.zip',
  'Autoruns': 'https://download.sysinternals.com/files/Autoruns.zip',
  'BleachBit': 'https://download.bleachbit.org/BleachBit-2.0-portable.zip',
  'BlueScreenView32': 'http://www.nirsoft.net/utils/bluescreenview.zip',
  'BlueScreenView64': 'http://www.nirsoft.net/utils/bluescreenview-x64.zip',
  'Caffeine': 'http://www.zhornsoftware.co.uk/caffeine/caffeine.zip',
  'ClassicStartSkin': 'http://www.classicshell.net/forum/download/file.php?id=3001&sid=9a195960d98fd754867dcb63d9315335',
  'Du': 'https://download.sysinternals.com/files/DU.zip',
  'ERUNT': 'http://www.aumha.org/downloads/erunt.zip',
  'Everything32': 'https://www.voidtools.com/Everything-1.4.1.935.x86.en-US.zip',
  'Everything64': 'https://www.voidtools.com/Everything-1.4.1.935.x64.en-US.zip',
  'FastCopy': 'https://fastcopy.jp/archive/FastCopy380_installer.exe',
  'Firefox uBO': 'https://addons.mozilla.org/firefox/downloads/file/1709472/ublock_origin-1.18.6-an+fx.xpi',
  'HitmanPro32': 'https://dl.surfright.nl/HitmanPro.exe',
  'HitmanPro64': 'https://dl.surfright.nl/HitmanPro_x64.exe',
  'HWiNFO': 'http://files2.majorgeeks.com/377527622c5325acc1cb937fb149d0de922320c0/systeminfo/hwi_602.zip',
  'Intel SSD Toolbox': r'https://downloadmirror.intel.com/28593/eng/Intel%20SSD%20Toolbox%20-%20v3.5.9.exe',
  'IOBit_Uninstaller': r'https://portableapps.com/redirect/?a=IObitUninstallerPortable&s=s&d=pa&f=IObitUninstallerPortable_7.5.0.7.paf.exe',
  'KVRT': 'http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe',
  'LibreOffice': 'https://download.documentfoundation.org/libreoffice/stable/6.2.4/win/x86_64/LibreOffice_6.2.4_Win_x64.msi',
  'Macs Fan Control': 'https://www.crystalidea.com/downloads/macsfancontrol_setup.exe',
  'NirCmd32': 'https://www.nirsoft.net/utils/nircmd.zip',
  'NirCmd64': 'https://www.nirsoft.net/utils/nircmd-x64.zip',
  'NotepadPlusPlus': 'https://notepad-plus-plus.org/repository/7.x/7.6.4/npp.7.6.4.bin.minimalist.7z',
  'Office Deployment Tool': 'https://download.microsoft.com/download/2/7/A/27AF1BE6-DD20-4CB4-B154-EBAB8A7D4A7E/officedeploymenttool_11509-33604.exe',
  'ProduKey32': 'http://www.nirsoft.net/utils/produkey.zip',
  'ProduKey64': 'http://www.nirsoft.net/utils/produkey-x64.zip',
  'PuTTY': 'https://the.earth.li/~sgtatham/putty/latest/w32/putty.zip',
  'RKill': 'https://www.bleepingcomputer.com/download/rkill/dl/10/',
  'Samsung Magician': 'https://s3.ap-northeast-2.amazonaws.com/global.semi.static/SAMSUNG_SSD_v5_3_0_181121/CD0C7CC1BE00525FAC4675B9E502899B41D5C3909ECE3AA2FB6B74A766B2A1EA/Samsung_Magician_Installer.zip',
  'SDIO Themes': 'http://snappy-driver-installer.org/downloads/SDIO_Themes.zip',
  'SDIO Torrent': 'http://snappy-driver-installer.org/downloads/SDIO_Update.torrent',
  'TDSSKiller': 'https://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe',
  'TestDisk': 'https://www.cgsecurity.org/testdisk-7.1-WIP.win.zip',
  'wimlib32': 'https://wimlib.net/downloads/wimlib-1.13.1-windows-i686-bin.zip',
  'wimlib64': 'https://wimlib.net/downloads/wimlib-1.13.1-windows-x86_64-bin.zip',
  'Winapp2': 'https://github.com/MoscaDotTo/Winapp2/archive/master.zip',
  'WizTree': 'https://antibody-software.com/files/wiztree_3_28_portable.zip',
  'XMPlay 7z': 'https://support.xmplay.com/files/16/xmp-7z.zip?v=800962',
  'XMPlay Game': 'https://support.xmplay.com/files/12/xmp-gme.zip?v=515637',
  'XMPlay RAR': 'https://support.xmplay.com/files/16/xmp-rar.zip?v=409646',
  'XMPlay WAModern': 'https://support.xmplay.com/files/10/WAModern.zip?v=207099',
  'XMPlay': 'https://support.xmplay.com/files/20/xmplay383.zip?v=298195',
  'XYplorerFree': 'https://www.xyplorer.com/download/xyplorer_free_noinstall.zip',
  }
VCREDIST_SOURCES = {
  '2010sp1': {
    '32': 'https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x86.exe',
    '64': 'https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe',
    },
  '2012u4': {
    '32': 'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe',
    '64': 'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe',
    },
  '2013': {
    '32': 'https://download.microsoft.com/download/0/5/6/056dcda9-d667-4e27-8001-8a0c6971d6b1/vcredist_x86.exe',
    '64': 'https://download.microsoft.com/download/0/5/6/056dcda9-d667-4e27-8001-8a0c6971d6b1/vcredist_x64.exe',
    },
  '2017': {
    '32': 'https://aka.ms/vs/15/release/vc_redist.x86.exe',
    '64': 'https://aka.ms/vs/15/release/vc_redist.x64.exe',
    },
  }
NINITE_REGEX = {
  'base': ['7-Zip', 'VLC'],
  'standard': ['Google Chrome', 'Mozilla Firefox', 'SumatraPDF'],
  'standard7': ['Google Chrome', 'Mozilla Firefox', 'SumatraPDF'],
  }
NINITE_SOURCES = {
  'Bundles': {
    'base.exe': '.net4.7.2-7zip-vlc',
    'base-standard.exe': '.net4.7.2-7zip-chrome-classicstart-firefox-sumatrapdf-vlc',
    'base-standard7.exe': '.net4.7.2-7zip-chrome-firefox-sumatrapdf-vlc',
    'standard.exe': 'chrome-classicstart-firefox-sumatrapdf',
    'standard7.exe': 'chrome-firefox-sumatrapdf',
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
    'Discord.exe': 'discord',
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
    'dotNET.exe': '.net4.7.2',
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
    'TeamViewer 14.exe': 'teamviewer14',
    'TeraCopy.exe': 'teracopy',
    'WinDirStat.exe': 'windirstat',
    },
  'Web Browsers': {
    'Google Chrome.exe': 'chrome',
    'Mozilla Firefox.exe': 'firefox',
    'Opera Chromium.exe': 'operaChromium',
    },
  }
RST_SOURCES = {
  #SetupRST_12.0.exe :  Removed from download center?
  #SetupRST_12.5.exe :  Removed from download center?
  #SetupRST_12.8.exe :  Removed from download center?
  'SetupRST_12.9.exe': 'https://downloadmirror.intel.com/23496/eng/SetupRST.exe',
  #SetupRST_13.x.exe :  Broken, doesn't support > .NET 4.5
  'SetupRST_14.0.exe': 'https://downloadmirror.intel.com/25091/eng/SetupRST.exe',
  'SetupRST_14.8.exe': 'https://downloadmirror.intel.com/26759/eng/setuprst.exe',
  'SetupRST_15.8.exe': 'https://downloadmirror.intel.com/27442/eng/SetupRST.exe',
  'SetupRST_15.9.exe': 'https://downloadmirror.intel.com/28656/eng/SetupRST.exe',
  #SetupRST_16.0.exe :  Deprecated by Intel
  #SetupRST_16.5.exe :  Deprecated by Intel
  #SetupRST_16.7.exe :  Deprecated by Intel
  'SetupRST_16.8.exe': 'https://downloadmirror.intel.com/28653/eng/SetupRST.exe',
  'SetupRST_17.2.exe': 'https://downloadmirror.intel.com/28650/eng/SetupRST.exe',
  }
WINDOWS_UPDATE_SOURCES = {
  '2999226': {
    # https://support.microsoft.com/en-us/help/2999226/update-for-universal-c-runtime-in-windows
    '7': {
      '32': 'https://download.microsoft.com/download/4/F/E/4FE73868-5EDD-4B47-8B33-CE1BB7B2B16A/Windows6.1-KB2999226-x86.msu',
      '64': 'https://download.microsoft.com/download/1/1/5/11565A9A-EA09-4F0A-A57E-520D5D138140/Windows6.1-KB2999226-x64.msu',
      },
    '8': {
      '32': 'https://download.microsoft.com/download/1/E/8/1E8AFE90-5217-464D-9292-7D0B95A56CE4/Windows8-RT-KB2999226-x86.msu',
      '64': 'https://download.microsoft.com/download/A/C/1/AC15393F-A6E6-469B-B222-C44B3BB6ECCC/Windows8-RT-KB2999226-x64.msu',
      },
    '8.1': {
      '32': 'https://download.microsoft.com/download/E/4/6/E4694323-8290-4A08-82DB-81F2EB9452C2/Windows8.1-KB2999226-x86.msu',
      '64': 'https://download.microsoft.com/download/9/6/F/96FD0525-3DDF-423D-8845-5F92F4A6883E/Windows8.1-KB2999226-x64.msu',
      },
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
