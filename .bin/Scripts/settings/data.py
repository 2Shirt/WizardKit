# Wizard Kit: Settings - Data

import ctypes
import re

# FastCopy
FAST_COPY_EXCLUDES = [
  r'\*.esd',
  r'\*.swm',
  r'\*.wim',
  r'\*.dd',
  r'\*.dd.tgz',
  r'\*.dd.txz',
  r'\*.map',
  r'\*.dmg',
  r'\*.image',
  r'$RECYCLE.BIN',
  r'$Recycle.Bin',
  r'.AppleDB',
  r'.AppleDesktop',
  r'.AppleDouble',
  r'.com.apple.timemachine.supported',
  r'.dbfseventsd',
  r'.DocumentRevisions-V100*',
  r'.DS_Store',
  r'.fseventsd',
  r'.PKInstallSandboxManager',
  r'.Spotlight*',
  r'.SymAV*',
  r'.symSchedScanLockxz',
  r'.TemporaryItems',
  r'.Trash*',
  r'.vol',
  r'.VolumeIcon.icns',
  r'desktop.ini',
  r'Desktop?DB',
  r'Desktop?DF',
  r'hiberfil.sys',
  r'lost+found',
  r'Network?Trash?Folder',
  r'pagefile.sys',
  r'Recycled',
  r'RECYCLER',
  r'System?Volume?Information',
  r'Temporary?Items',
  r'Thumbs.db',
  ]
FAST_COPY_ARGS = [
  '/cmd=noexist_only',
  '/utf8',
  '/skip_empty_dir',
  '/linkdest',
  '/no_ui',
  '/auto_close',
  '/exclude={}'.format(';'.join(FAST_COPY_EXCLUDES)),
  ]

# Regex
REGEX_EXCL_ITEMS = re.compile(
  r'^(\.(AppleDB|AppleDesktop|AppleDouble'
  r'|com\.apple\.timemachine\.supported|dbfseventsd'
  r'|DocumentRevisions-V100.*|DS_Store|fseventsd|PKInstallSandboxManager'
  r'|Spotlight.*|SymAV.*|symSchedScanLockxz|TemporaryItems|Trash.*'
  r'|vol|VolumeIcon\.icns)|desktop\.(ini|.*DB|.*DF)'
  r'|(hiberfil|pagefile)\.sys|lost\+found|Network\.*Trash\.*Folder'
  r'|Recycle[dr]|System\.*Volume\.*Information|Temporary\.*Items'
  r'|Thumbs\.db)$',
  re.IGNORECASE)
REGEX_EXCL_ROOT_ITEMS = re.compile(
  r'^(boot(mgr|nxt)$|Config.msi'
  r'|(eula|globdata|install|vc_?red)'
  r'|.*.sys$|System Volume Information|RECYCLER?|\$Recycle\.bin'
  r'|\$?Win(dows(.old.*|\.  BT|)$|RE_)|\$GetCurrent|Windows10Upgrade'
  r'|PerfLogs|Program Files|SYSTEM.SAV'
  r'|.*\.(esd|swm|wim|dd|map|dmg|image)$)',
  re.IGNORECASE)
REGEX_INCL_ROOT_ITEMS = re.compile(
  r'^(AdwCleaner|(My\s*|)(Doc(uments?( and Settings|)|s?)|Downloads'
  r'|Media|Music|Pic(ture|)s?|Vid(eo|)s?)'
  r'|{prefix}(-?Info|-?Transfer|)'
  r'|(ProgramData|Recovery|Temp.*|Users)$'
  r'|.*\.(log|txt|rtf|qb\w*|avi|m4a|m4v|mp4|mkv|jpg|png|tiff?)$)'
  r''.format(prefix=KIT_NAME_SHORT),
  re.IGNORECASE)
REGEX_WIM_FILE = re.compile(
  r'\.wim$',
  re.IGNORECASE)
REGEX_WINDOWS_OLD = re.compile(
  r'^Win(dows|)\.old',
  re.IGNORECASE)

# Thread error modes
## Code borrowed from: https://stackoverflow.com/a/29075319
SEM_NORMAL = ctypes.c_uint()
SEM_FAILCRITICALERRORS = 1
SEM_NOOPENFILEERRORBOX = 0x8000
SEM_FAIL = SEM_NOOPENFILEERRORBOX | SEM_FAILCRITICALERRORS


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
