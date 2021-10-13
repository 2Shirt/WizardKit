"""WizardKit: Config - Tool Sources"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2


# Download frequency in days
DOWNLOAD_FREQUENCY = 7


# Sources
SOURCES = {
  # Main
  'AVRemover32':        'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt32_enu.exe',
  'AVRemover64':        'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt64_enu.exe',
  'AdwCleaner':         'https://downloads.malwarebytes.com/file/adwcleaner',
  'Autologon32':        'http://live.sysinternals.com/Autologon.exe',
  'Autologon64':        'http://live.sysinternals.com/Autologon64.exe',
  'Firefox32':          'https://download.mozilla.org/?product=firefox-latest-ssl&os=win&lang=en-US',
  'Firefox64':          'https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=en-US',
  'Fluent-Metro':       'https://github.com/bonzibudd/Fluent-Metro/releases/download/v1.5.2/Fluent-Metro_1.5.2.zip',
  'HitmanPro32':        'https://dl.surfright.nl/HitmanPro.exe',
  'HitmanPro64':        'https://dl.surfright.nl/HitmanPro_x64.exe',
  'KVRT':               'https://devbuilds.s.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe',
  'OpenShell':          'https://github.com/Open-Shell/Open-Shell-Menu/releases/download/v4.4.160/OpenShellSetup_4_4_160.exe',
  'RKill':              'https://download.bleepingcomputer.com/grinler/rkill.exe',
  'RegDelNull':         'https://live.sysinternals.com/RegDelNull.exe',
  'RegDelNull64':       'https://live.sysinternals.com/RegDelNull64.exe',
  'Software Bundle':    'https://ninite.com/.net4.8-7zip-chrome-edge-vlc/ninite.exe',
  'TDSSKiller':         'https://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe',
  'VCRedist_2012_x32':  'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe',
  'VCRedist_2012_x64':  'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe',
  'VCRedist_2013_x32':  'https://aka.ms/highdpimfc2013x86enu',
  'VCRedist_2013_x64':  'https://aka.ms/highdpimfc2013x64enu',
  'VCRedist_2019_x32':  'https://aka.ms/vs/16/release/vc_redist.x86.exe',
  'VCRedist_2019_x64':  'https://aka.ms/vs/16/release/vc_redist.x64.exe',

  # Build Kit
  'AIDA64':             'https://download.aida64.com/aida64engineer633.zip',
  'Adobe Reader DC':    'https://ardownload2.adobe.com/pub/adobe/reader/win/AcrobatDC/2100720091/AcroRdrDC2100720091_en_US.exe',
  'Autoruns32':         'http://live.sysinternals.com/Autoruns.exe',
  'Autoruns64':         'http://live.sysinternals.com/Autoruns64.exe',
  'Aria2':              'https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0-win-32bit-build1.zip',
  'BleachBit':          'https://download.bleachbit.org/BleachBit-4.4.0-portable.zip',
  'BlueScreenView32':   'http://www.nirsoft.net/utils/bluescreenview.zip',
  'BlueScreenView64':   'http://www.nirsoft.net/utils/bluescreenview-x64.zip',
  'ERUNT':              'http://www.aumha.org/downloads/erunt.zip',
  'Everything32':       'https://www.voidtools.com/Everything-1.4.1.1009.x86.en-US.zip',
  'Everything64':       'https://www.voidtools.com/Everything-1.4.1.1009.x64.en-US.zip',
  'FastCopy':           'https://ftp.vector.co.jp/73/10/2323/FastCopy392_installer.exe',
  'FurMark':            'https://geeks3d.com/dl/get/569',
  'HWiNFO':             'https://www.sac.sk/download/utildiag/hwi_712.zip',
  'IOBit Uninstaller':  'https://portableapps.com/redirect/?a=IObitUninstallerPortable&s=s&d=pa&f=IObitUninstallerPortable_7.5.0.7.paf.exe',
  'LibreOffice32':      'https://download.documentfoundation.org/libreoffice/stable/7.2.1/win/x86/LibreOffice_7.2.1_Win_x86.msi',
  'LibreOffice64':      'https://download.documentfoundation.org/libreoffice/stable/7.2.1/win/x86_64/LibreOffice_7.2.1_Win_x64.msi',
  'Macs Fan Control':   'https://www.crystalidea.com/downloads/macsfancontrol_setup.exe',
  'Neutron':            'http://keir.net/download/neutron.zip',
  'Notepad++':          'https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.1.5/npp.8.1.5.portable.minimalist.7z',
  'PuTTY':              'https://the.earth.li/~sgtatham/putty/latest/w32/putty.zip',
  'SDIO Torrent':       'http://snappy-driver-installer.org/downloads/SDIO_Update.torrent',
  'TestDisk':           'https://www.cgsecurity.org/testdisk-7.2-WIP.win.zip',
  'WizTree':            'https://wiztreefree.com/files/wiztree_3_39_portable.zip',
  'XMPlay':             'https://support.xmplay.com/files/20/xmplay385.zip?v=47090',
  'XMPlay 7z':          'https://support.xmplay.com/files/16/xmp-7z.zip?v=800962',
  'XMPlay Game':        'https://support.xmplay.com/files/12/xmp-gme.zip?v=515637',
  'XMPlay RAR':         'https://support.xmplay.com/files/16/xmp-rar.zip?v=409646',
  'XMPlay Innocuous':   'https://support.xmplay.com/files/10/Innocuous%20(v1.4).zip?v=594785',
}


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
