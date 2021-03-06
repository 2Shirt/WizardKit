"""WizardKit: Config - Tools"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2


# Download frequency in days
DOWNLOAD_FREQUENCY = 7


# Sources
SOURCES = {
  'Adobe Reader DC': 'https://ardownload2.adobe.com/pub/adobe/reader/win/AcrobatDC/2100120145/AcroRdrDC2100120145_en_US.exe',
  'AdwCleaner': 'https://downloads.malwarebytes.com/file/adwcleaner',
  'AIDA64': 'https://download.aida64.com/aida64engineer633.zip',
  'aria2': 'https://github.com/aria2/aria2/releases/download/release-1.35.0/aria2-1.35.0-win-32bit-build1.zip',
  'Autologon32': 'http://live.sysinternals.com/Autologon.exe',
  'Autologon64': 'http://live.sysinternals.com/Autologon64.exe',
  'Autoruns': 'https://download.sysinternals.com/files/Autoruns.zip',
  'AVRemover32': 'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt32_enu.exe',
  'AVRemover64': 'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt64_enu.exe',
  'BleachBit': 'https://download.bleachbit.org/BleachBit-4.2.0-portable.zip',
  'BlueScreenView32': 'http://www.nirsoft.net/utils/bluescreenview.zip',
  'BlueScreenView64': 'http://www.nirsoft.net/utils/bluescreenview-x64.zip',
  'Caffeine': 'http://www.zhornsoftware.co.uk/caffeine/caffeine.zip',
  'ClassicStartSkin': 'http://www.classicshell.net/forum/download/file.php?id=3001&sid=9a195960d98fd754867dcb63d9315335',
  'Du': 'https://download.sysinternals.com/files/DU.zip',
  'ERUNT': 'http://www.aumha.org/downloads/erunt.zip',
  'ESET NOD32 AV': 'https://download.eset.com/com/eset/apps/home/eav/windows/latest/eav_nt64.exe',
  'ESET Online Scanner': 'https://download.eset.com/com/eset/tools/online_scanner/latest/esetonlinescanner_enu.exe',
  'Everything32': 'https://www.voidtools.com/Everything-1.4.1.1005.x86.en-US.zip',
  'Everything64': 'https://www.voidtools.com/Everything-1.4.1.1005.x64.en-US.zip',
  'FastCopy': 'https://ftp.vector.co.jp/73/10/2323/FastCopy392_installer.exe',
  'FurMark': 'https://geeks3d.com/dl/get/569',
  'Firefox uBO': 'https://addons.mozilla.org/firefox/downloads/file/3740966/ublock_origin-1.34.0-an+fx.xpi',
  'HitmanPro': 'https://dl.surfright.nl/HitmanPro.exe',
  'HitmanPro64': 'https://dl.surfright.nl/HitmanPro_x64.exe',
  'HWiNFO': 'https://files1.majorgeeks.com/c8a055180587599139f8f454712dcc618cd1740e/systeminfo/hwi_702.zip',
  'Intel SSD Toolbox': r'https://downloadmirror.intel.com/28593/eng/Intel%20SSD%20Toolbox%20-%20v3.5.9.exe',
  'IOBit_Uninstaller': r'https://portableapps.com/redirect/?a=IObitUninstallerPortable&s=s&d=pa&f=IObitUninstallerPortable_7.5.0.7.paf.exe',
  'KVRT': 'https://devbuilds.s.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe',
  'LibreOffice': 'https://download.documentfoundation.org/libreoffice/stable/7.1.2/win/x86_64/LibreOffice_7.1.2_Win_x64.msi',
  'Linux Reader': 'https://www.diskinternals.com/download/Linux_Reader.exe',
  'Macs Fan Control': 'https://www.crystalidea.com/downloads/macsfancontrol_setup.exe',
  'NirCmd32': 'https://www.nirsoft.net/utils/nircmd.zip',
  'NirCmd64': 'https://www.nirsoft.net/utils/nircmd-x64.zip',
  'NotepadPlusPlus': 'https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v7.9.5/npp.7.9.5.portable.minimalist.7z',
  'Office Deployment Tool': 'https://download.microsoft.com/download/2/7/A/27AF1BE6-DD20-4CB4-B154-EBAB8A7D4A7E/officedeploymenttool_11617-33601.exe',
  'ProduKey32': 'http://www.nirsoft.net/utils/produkey.zip',
  'ProduKey64': 'http://www.nirsoft.net/utils/produkey-x64.zip',
  'PuTTY': 'https://the.earth.li/~sgtatham/putty/latest/w32/putty.zip',
  'RegDelNull': 'https://download.sysinternals.com/files/Regdelnull.zip',
  'RKill': 'https://download.bleepingcomputer.com/grinler/rkill.exe',
  'Samsung Magician': 'https://s3.ap-northeast-2.amazonaws.com/global.semi.static/SAMSUNG_SSD_v5_3_0_181121/CD0C7CC1BE00525FAC4675B9E502899B41D5C3909ECE3AA2FB6B74A766B2A1EA/Samsung_Magician_Installer.zip',
  'SDIO Themes': 'http://snappy-driver-installer.org/downloads/SDIO_Themes.zip',
  'SDIO Torrent': 'http://snappy-driver-installer.org/downloads/SDIO_Update.torrent',
  'ShutUp10': 'https://dl5.oo-software.com/files/ooshutup10/OOSU10.exe',
  'smartmontools': 'https://1278-105252244-gh.circle-artifacts.com/0/builds/smartmontools-win32-setup-7.3-r5216.exe',
  'TDSSKiller': 'https://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe',
  'TestDisk': 'https://www.cgsecurity.org/testdisk-7.2-WIP.win.zip',
  'wimlib32': 'https://wimlib.net/downloads/wimlib-1.13.3-windows-i686-bin.zip',
  'wimlib64': 'https://wimlib.net/downloads/wimlib-1.13.3-windows-x86_64-bin.zip',
  'WinAIO Repair': 'http://www.tweaking.com/files/setups/tweaking.com_windows_repair_aio.zip',
  'Winapp2': 'https://github.com/MoscaDotTo/Winapp2/archive/master.zip',
  'WizTree': 'https://wiztreefree.com/files/wiztree_3_39_portable.zip',
  'XMPlay 7z': 'https://support.xmplay.com/files/16/xmp-7z.zip?v=800962',
  'XMPlay Game': 'https://support.xmplay.com/files/12/xmp-gme.zip?v=515637',
  'XMPlay RAR': 'https://support.xmplay.com/files/16/xmp-rar.zip?v=409646',
  'XMPlay WAModern': 'https://support.xmplay.com/files/10/WAModern.zip?v=207099',
  'XMPlay': 'https://support.xmplay.com/files/20/xmplay383.zip?v=298195',
  'XYplorerFree': 'https://www.xyplorer.com/download/xyplorer_free_noinstall.zip',
}


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
