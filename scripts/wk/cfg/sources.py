"""WizardKit: Config - Sources"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2


# Download frequency in days
DOWNLOAD_FREQUENCY = 7


# Sources
SOURCES = {
  'AIDA64': 'https://download.aida64.com/aida64engineer633.zip',
  'AVRemover32': 'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt32_enu.exe',
  'AVRemover64': 'https://download.eset.com/com/eset/tools/installers/av_remover/latest/avremover_nt64_enu.exe',
  'AdwCleaner': 'https://downloads.malwarebytes.com/file/adwcleaner',
  'Autologon32': 'http://live.sysinternals.com/Autologon.exe',
  'Autologon64': 'http://live.sysinternals.com/Autologon64.exe',
  'BleachBit': 'https://download.bleachbit.org/BleachBit-4.2.0-portable.zip',
  'BlueScreenView32': 'http://www.nirsoft.net/utils/bluescreenview.zip',
  'BlueScreenView64': 'http://www.nirsoft.net/utils/bluescreenview-x64.zip',
  'Firefox32': 'https://download.mozilla.org/?product=firefox-latest-ssl&os=win&lang=en-US',
  'Firefox64': 'https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=en-US',
  'Fluent-Metro': 'https://github.com/bonzibudd/Fluent-Metro/releases/download/v1.5.2/Fluent-Metro_1.5.2.zip',
  'HitmanPro32': 'https://dl.surfright.nl/HitmanPro.exe',
  'HitmanPro64': 'https://dl.surfright.nl/HitmanPro_x64.exe',
  'KVRT': 'https://devbuilds.s.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe',
  'LibreOffice': 'https://download.documentfoundation.org/libreoffice/stable/7.1.2/win/x86_64/LibreOffice_7.1.2_Win_x64.msi',
  'OpenShell': 'https://github.com/Open-Shell/Open-Shell-Menu/releases/download/v4.4.160/OpenShellSetup_4_4_160.exe',
  'RegDelNull': 'https://download.sysinternals.com/files/Regdelnull.zip',
  'RKill': 'https://download.bleepingcomputer.com/grinler/rkill.exe',
  'Software Bundle': 'https://ninite.com/.net4.8-7zip-chrome-edge-vlc/ninite.exe',
  'TDSSKiller': 'https://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe',
  'VCRedist_2012_x32': 'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe',
  'VCRedist_2012_x64': 'https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe',
  'VCRedist_2013_x32': 'https://aka.ms/highdpimfc2013x86enu',
  'VCRedist_2013_x64': 'https://aka.ms/highdpimfc2013x64enu',
  'VCRedist_2019_x32': 'https://aka.ms/vs/16/release/vc_redist.x86.exe',
  'VCRedist_2019_x64': 'https://aka.ms/vs/16/release/vc_redist.x64.exe',
}


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
