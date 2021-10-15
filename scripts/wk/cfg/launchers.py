"""WizardKit: Config - Launchers (Windows)"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2

LAUNCHERS = {
  r'': { # Root Dir
    'Auto Repairs': {
      'L_TYPE': 'PyScript',
      'L_PATH': 'Scripts',
      'L_ITEM': 'auto_repairs.py',
      'L_ELEV': 'True',
      },
    'Auto Setup': {
      'L_TYPE': 'PyScript',
      'L_PATH': 'Scripts',
      'L_ITEM': 'auto_setup.py',
      'L_ELEV': 'True',
      },
    },
  r'Data Recovery': {
    'PhotoRec (CLI)': {
      'L_TYPE': 'Executable',
      'L_PATH': 'TestDisk',
      'L_ITEM': 'photorec_win.exe',
      'L_ELEV': 'True',
      'L__CLI': 'True',
      },
    'PhotoRec': {
      'L_TYPE': 'Executable',
      'L_PATH': 'TestDisk',
      'L_ITEM': 'qphotorec_win.exe',
      'L_ELEV': 'True',
      },
    'TestDisk': {
      'L_TYPE': 'Executable',
      'L_PATH': 'TestDisk',
      'L_ITEM': 'testdisk_win.exe',
      'L_ELEV': 'True',
      'L__CLI': 'True',
      },
    },
  r'Data Transfers': {
    'FastCopy (as ADMIN)': {
      'L_TYPE': 'Executable',
      'L_PATH': 'FastCopy',
      'L_ITEM': 'FastCopy.exe',
      'L_ARGS': (
        r' /logfile=%log_dir%\Tools\FastCopy.log'
        r' /cmd=noexist_only'
        r' /utf8'
        r' /skip_empty_dir'
        r' /linkdest'
        r' /exclude='
          r'$RECYCLE.BIN;'
          r'$Recycle.Bin;'
          r'.AppleDB;'
          r'.AppleDesktop;'
          r'.AppleDouble;'
          r'.com.apple.timemachine.supported;'
          r'.dbfseventsd;'
          r'.DocumentRevisions-V100*;'
          r'.DS_Store;'
          r'.fseventsd;'
          r'.PKInstallSandboxManager;'
          r'.Spotlight*;'
          r'.SymAV*;'
          r'.symSchedScanLockxz;'
          r'.TemporaryItems;'
          r'.Trash*;'
          r'.vol;'
          r'.VolumeIcon.icns;'
          r'desktop.ini;'
          r'Desktop?DB;'
          r'Desktop?DF;'
          r'hiberfil.sys;'
          r'lost+found;'
          r'Network?Trash?Folder;'
          r'pagefile.sys;'
          r'Recycled;'
          r'RECYCLER;'
          r'System?Volume?Information;'
          r'Temporary?Items;'
          r'Thumbs.db'
        r' /to=%client_dir%\Transfer_%iso_date%\ '
        ),
      'L_ELEV': 'True',
      'Extra Code': [
        r'call "%bin%\Scripts\init_client_dir.cmd" /Logs /Transfer',
        ],
      },
    'FastCopy': {
      'L_TYPE': 'Executable',
      'L_PATH': 'FastCopy',
      'L_ITEM': 'FastCopy.exe',
      'L_ARGS': (
        r' /logfile=%log_dir%\Tools\FastCopy.log'
        r' /cmd=noexist_only'
        r' /utf8'
        r' /skip_empty_dir'
        r' /linkdest'
        r' /exclude='
          r'$RECYCLE.BIN;'
          r'$Recycle.Bin;'
          r'.AppleDB;'
          r'.AppleDesktop;'
          r'.AppleDouble;'
          r'.com.apple.timemachine.supported;'
          r'.dbfseventsd;'
          r'.DocumentRevisions-V100*;'
          r'.DS_Store;'
          r'.fseventsd;'
          r'.PKInstallSandboxManager;'
          r'.Spotlight*;'
          r'.SymAV*;'
          r'.symSchedScanLockxz;'
          r'.TemporaryItems;'
          r'.Trash*;'
          r'.vol;'
          r'.VolumeIcon.icns;'
          r'desktop.ini;'
          r'Desktop?DB;'
          r'Desktop?DF;'
          r'hiberfil.sys;'
          r'lost+found;'
          r'Network?Trash?Folder;'
          r'pagefile.sys;'
          r'Recycled;'
          r'RECYCLER;'
          r'System?Volume?Information;'
          r'Temporary?Items;'
          r'Thumbs.db'
        r' /to=%client_dir%\Transfer_%iso_date%\ '
        ),
      'Extra Code': [
        r'call "%bin%\Scripts\init_client_dir.cmd" /Logs /Transfer',
        ],
      },
    },
  r'Diagnostics': {
    'AIDA64': {
      'L_TYPE': 'Executable',
      'L_PATH': 'AIDA64',
      'L_ITEM': 'aida64.exe',
      },
    'Autoruns (with VirusTotal Scan)': {
      'L_TYPE': 'Executable',
      'L_PATH': 'Sysinternals',
      'L_ITEM': 'Autoruns.exe',
      'L_ARGS': '-e',
      'Extra Code': [
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v checkvirustotal /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v shownomicrosoft /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v shownowindows /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v showonlyvirustotal /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v submitvirustotal /t REG_DWORD /d 0 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns /v verifysignatures /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns\SigCheck /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns\Streams /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
        r'reg add HKCU\Software\Sysinternals\AutoRuns\VirusTotal /v VirusTotalTermsAccepted /t REG_DWORD /d 1 /f >nul',
        ],
      },
    'BleachBit': {
      'L_TYPE': 'Executable',
      'L_PATH': 'BleachBit',
      'L_ITEM': 'bleachbit.exe',
      },
    'BlueScreenView': {
      'L_TYPE': 'Executable',
      'L_PATH': 'BlueScreenView',
      'L_ITEM': 'BlueScreenView.exe',
      },
    'ERUNT': {
      'L_TYPE': 'Executable',
      'L_PATH': 'erunt',
      'L_ITEM': 'ERUNT.EXE',
      'L_ARGS': r'%client_dir%\Backups\Registry\%iso_date% sysreg curuser otherusers',
      'L_ELEV': 'True',
      'Extra Code': [
        r'call "%bin%\Scripts\init_client_dir.cmd" /Logs',
        ],
      },
    'FurMark': {
      'L_TYPE': 'Executable',
      'L_PATH': 'FurMark',
      'L_ITEM': 'FurMark.exe',
      },
    'HWiNFO': {
      'L_TYPE': 'Executable',
      'L_PATH': 'HWiNFO',
      'L_ITEM': 'HWiNFO.exe',
      'Extra Code': [
        r'for %%a in (32 64) do (',
        r'  copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
        r'  (echo SensorsOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
        r'  (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
        r')',
        ],
      },
    'HWiNFO (Sensors)': {
      'L_TYPE': 'Executable',
      'L_PATH': 'HWiNFO',
      'L_ITEM': 'HWiNFO.exe',
      'Extra Code': [
        r'for %%a in (32 64) do (',
        r'  copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
        r'  (echo SensorsOnly=1)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
        r'  (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
        r')',
        ],
      },
    'Snappy Driver Installer Origin': {
      'L_TYPE': 'Executable',
      'L_PATH': 'SDIO',
      'L_ITEM': 'SDIO.exe',
      },
    },
  r'Misc': {
    'ConEmu (as ADMIN)': {
      'L_TYPE': 'Executable',
      'L_PATH': 'ConEmu',
      'L_ITEM': 'ConEmu.exe',
      'L_ELEV': 'True',
      },
    'ConEmu': {
      'L_TYPE': 'Executable',
      'L_PATH': 'ConEmu',
      'L_ITEM': 'ConEmu.exe',
      },
    'Everything': {
      'L_TYPE': 'Executable',
      'L_PATH': 'Everything',
      'L_ITEM': 'Everything.exe',
      'L_ARGS': '-nodb',
      'L_ELEV': 'True',
      },
    'Notepad++': {
      'L_TYPE': 'Executable',
      'L_PATH': 'notepadplusplus',
      'L_ITEM': 'notepadplusplus.exe',
      },
    'PuTTY': {
      'L_TYPE': 'Executable',
      'L_PATH': 'PuTTY',
      'L_ITEM': 'PUTTY.EXE',
      },
    'WizTree': {
      'L_TYPE': 'Executable',
      'L_PATH': 'WizTree',
      'L_ITEM': 'WizTree.exe',
      'L_ELEV': 'True',
      },
    'XMPlay': {
      'L_TYPE': 'Executable',
      'L_PATH': 'XMPlay',
      'L_ITEM': 'xmplay.exe',
      'L_ARGS': r'"%bin%\XMPlay\music.7z"',
      },
    },
  r'Uninstallers': {
    'IObit Uninstaller': {
      'L_TYPE': 'Executable',
      'L_PATH': 'IObitUninstallerPortable',
      'L_ITEM': 'IObitUninstallerPortable.exe',
      },
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
