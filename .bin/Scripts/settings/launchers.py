# Wizard Kit: Settings - Launchers

LAUNCHERS = {
    r'(Root)': {
        'Activate Windows': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'activate.py',
            'L_ELEV': 'True',
            },
        'Enter SafeMode': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'safemode_enter.py',
            'L_ELEV': 'True',
            },
        'Exit SafeMode': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'safemode_exit.py',
            'L_ELEV': 'True',
            },
        'System Checklist': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'system_checklist.py',
            'L_ELEV': 'True',
            },
        'System Diagnostics': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'system_diagnostics.py',
            'L_ELEV': 'True',
            },
        'User Checklist': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'user_checklist.py',
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
                r' /logfile=%log_dir%\FastCopy.log'
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
                r'call "%bin%\Scripts\init_client_dir.cmd" /Info /Transfer',
                ],
            },
        'FastCopy': {
            'L_TYPE': 'Executable',
            'L_PATH': 'FastCopy',
            'L_ITEM': 'FastCopy.exe',
            'L_ARGS': (
                r' /logfile=%log_dir%\FastCopy.log'
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
                r'call "%bin%\Scripts\init_client_dir.cmd" /Info /Transfer',
                ],
            },
        'KVRT': {
            'L_TYPE': 'Executable',
            'L_PATH': 'KVRT',
            'L_ITEM': 'KVRT.exe',
            'L_ARGS': (
                r' -accepteula'
                r' -d %q_dir%'
                r' -processlevel 3'
                r' -dontcryptsupportinfo'
                r' -fixednames'
                ),
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Quarantine',
                r'set "q_dir=%client_dir%\Quarantine\KVRT"',
                r'mkdir "%q_dir%">nul 2>&1',
                ],
            },
        'Transferred Keys': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'transferred_keys.py',
            'L_ELEV': 'True',
            },
        'User Data Transfer': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'user_data_transfer.py',
            'L_ELEV': 'True',
            },
        'XYplorer (as ADMIN)': {
            'L_TYPE': 'Executable',
            'L_PATH': 'XYplorerFree',
            'L_ITEM': 'XYplorerFree.exe',
            'L_ARGS': r'/exp /win=max %userprofile%',
            'L_ELEV': 'True',
            },
        'XYplorer': {
            'L_TYPE': 'Executable',
            'L_PATH': 'XYplorerFree',
            'L_ITEM': 'XYplorerFree.exe',
            'L_ARGS': r'/exp /win=max %userprofile%',
            },
        },
    r'Diagnostics': {
        'HWiNFO': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HWiNFO',
            'L_ITEM': 'HWiNFO.exe',
            'Extra Code': [
                r'for %%a in (32 64) do (',
                r'    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SensorsOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r')',
                ],
            },
        'ProduKey': {
            'L_TYPE': 'Executable',
            'L_PATH': 'ProduKey',
            'L_ITEM': 'ProduKey.exe',
            'L_ELEV': 'True',
            'Extra Code': [
                r'if exist "%bin%\ProduKey" (',
                r'    del "%bin%\ProduKey\ProduKey.cfg" 2>nul',
                r'    del "%bin%\ProduKey\ProduKey64.cfg" 2>nul',
                r')',
                ],
            },
        },
    r'Diagnostics\Extras': {
        'AIDA64': {
            'L_TYPE': 'Executable',
            'L_PATH': 'AIDA64',
            'L_ITEM': 'aida64.exe',
            },
        'Autoruns (with VirusTotal Scan)': {
            'L_TYPE': 'Executable',
            'L_PATH': 'Autoruns',
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
            'L_ARGS': '%client_dir%\Backups\%iso_date%\Registry sysreg curuser otherusers',
            'L_ELEV': 'True',
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Info',
                ],
            },
        'HitmanPro': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HitmanPro',
            'L_ITEM': 'HitmanPro.exe',
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Info',
                ],
            },
        'HWiNFO (Sensors)': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HWiNFO',
            'L_ITEM': 'HWiNFO.exe',
            'Extra Code': [
                r'for %%a in (32 64) do (',
                r'    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SensorsOnly=1)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r')',
                ],
            },
        },
    r'Drivers': {
        'Intel RST (Current Release)': {
            'L_TYPE': 'Executable',
            'L_PATH': '_Drivers\Intel RST',
            'L_ITEM': 'SetupRST_15.9.exe',
            'L_7ZIP': 'SetupRST_15.9.exe',
            },
        'Intel RST (Previous Releases)': {
            'L_TYPE': 'Folder',
            'L_PATH': '_Drivers\Intel RST',
            'L_ITEM': '.',
            'L_NCMD': 'True',
            },
        'Intel SSD Toolbox': {
            'L_TYPE': 'Executable',
            'L_PATH': r'_Drivers\Intel SSD Toolbox',
            'L_ITEM': 'Intel SSD Toolbox.exe',
            },
        'Samsing Magician': {
            'L_TYPE': 'Executable',
            'L_PATH': r'_Drivers\Samsung Magician',
            'L_ITEM': 'Samsung Magician.exe',
            },
        'Snappy Driver Installer Origin': {
            'L_TYPE': 'Executable',
            'L_PATH': '_Drivers\SDIO',
            'L_ITEM': 'SDIO.exe',
            },
        },
    r'Drivers\Extras': {
        'Acer': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HWiNFO',
            'L_ITEM': 'HWiNFO.exe',
            'Extra Code': [
                r'for %%a in (32 64) do (',
                r'    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SensorsOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r')',
                r'start "" "http://us.acer.com/ac/en/US/content/drivers"',
                ],
            },
        'Lenovo': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HWiNFO',
            'L_ITEM': 'HWiNFO.exe',
            'Extra Code': [
                r'for %%a in (32 64) do (',
                r'    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SensorsOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r')',
                r'start "" "https://pcsupport.lenovo.com/us/en/"',
                ],
            },
        'Toshiba': {
            'L_TYPE': 'Executable',
            'L_PATH': 'HWiNFO',
            'L_ITEM': 'HWiNFO.exe',
            'Extra Code': [
                r'for %%a in (32 64) do (',
                r'    copy /y "%bin%\HWiNFO\general.ini" "%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SensorsOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r'    (echo SummaryOnly=0)>>"%bin%\HWiNFO\HWiNFO%%a.ini"',
                r')',
                r'start "" "http://support.toshiba.com/drivers"',
                ],
            },
        },
    r'Installers': {
        'SW Bundle': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'install_sw_bundle.py',
            'L_ELEV': 'True',
            },
        },
    r'Installers\Extras\Office\2013': {
        'Home and Business 2013 (x32)': {
            'L_TYPE': 'Office',
            'L_PATH': '2013',
            'L_ITEM': 'hb_32.xml',
            'L_NCMD': 'True',
            },
        'Home and Business 2013 (x64)': {
            'L_TYPE': 'Office',
            'L_PATH': '2013',
            'L_ITEM': 'hb_64.xml',
            'L_NCMD': 'True',
            },
        'Home and Student 2013 (x32)': {
            'L_TYPE': 'Office',
            'L_PATH': '2013',
            'L_ITEM': 'hs_32.xml',
            'L_NCMD': 'True',
            },
        'Home and Student 2013 (x64)': {
            'L_TYPE': 'Office',
            'L_PATH': '2013',
            'L_ITEM': 'hs_64.xml',
            'L_NCMD': 'True',
            },
        },
    r'Installers\Extras\Office\2016': {
        'Home and Business 2016 (x32)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': 'hb_32.xml',
            'L_NCMD': 'True',
            },
        'Home and Business 2016 (x64)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': 'hb_64.xml',
            'L_NCMD': 'True',
            },
        'Home and Student 2016 (x32)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': 'hs_32.xml',
            'L_NCMD': 'True',
            },
        'Home and Student 2016 (x64)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': 'hs_64.xml',
            'L_NCMD': 'True',
            },
        'Office 365 2016 (x32)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': '365_32.xml',
            'L_NCMD': 'True',
            },
        'Office 365 2016 (x64)': {
            'L_TYPE': 'Office',
            'L_PATH': '2016',
            'L_ITEM': '365_64.xml',
            'L_NCMD': 'True',
            },
        },
    r'Installers\Extras\Runtimes': {
        'Visual C++ Runtimes': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'install_vcredists.py',
            'L_ELEV': 'True',
            },
        },
    r'Misc': {
        'Cleanup CBS Temp Files': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'cbs_fix.py',
            'L_ELEV': 'True',
            },
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
        'TreeSizeFree': {
            'L_TYPE': 'Executable',
            'L_PATH': 'TreeSizeFree',
            'L_ITEM': 'TreeSizeFree.exe',
            'L_ELEV': 'True',
            },
        'Update Kit': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'update_kit.py',
            },
        'XMPlay': {
            'L_TYPE': 'Executable',
            'L_PATH': 'XMPlay',
            'L_ITEM': 'xmplay.exe',
            'L_ARGS': '"%bin%\XMPlay\music.7z"',
            },
        },
    r'Repairs': {
        'AdwCleaner': {
            'L_TYPE': 'Executable',
            'L_PATH': 'AdwCleaner',
            'L_ITEM': 'AdwCleaner.exe',
            },
        'Autoruns': {
            'L_TYPE': 'Executable',
            'L_PATH': 'Autoruns',
            'L_ITEM': 'Autoruns.exe',
            'L_ARGS': '-e',
            'Extra Code': [
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v checkvirustotal /t REG_DWORD /d 0 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v shownomicrosoft /t REG_DWORD /d 1 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v shownowindows /t REG_DWORD /d 1 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v showonlyvirustotal /t REG_DWORD /d 0 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v submitvirustotal /t REG_DWORD /d 0 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns /v verifysignatures /t REG_DWORD /d 0 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns\SigCheck /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns\Streams /v EulaAccepted /t REG_DWORD /d 1 /f >nul',
                r'reg add HKCU\Software\Sysinternals\AutoRuns\VirusTotal /v VirusTotalTermsAccepted /t REG_DWORD /d 1 /f >nul',
                ],
            },
        'CHKDSK': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'check_disk.py',
            'L_ELEV': 'True',
            },
        'DISM': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'dism.py',
            'L_ELEV': 'True',
            },
        'KVRT': {
            'L_TYPE': 'Executable',
            'L_PATH': 'KVRT',
            'L_ITEM': 'KVRT.exe',
            'L_ARGS': (
                r' -accepteula'
                r' -d %q_dir%'
                r' -processlevel 3'
                r' -dontcryptsupportinfo'
                r' -fixednames'
                ),
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Quarantine',
                r'set "q_dir=%client_dir%\Quarantine\KVRT"',
                r'mkdir "%q_dir%">nul 2>&1',
                ],
            },
        'RKill': {
            'L_TYPE': 'Executable',
            'L_PATH': 'RKill',
            'L_ITEM': 'RKill.exe',
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Info',
                ],
            },
        'SFC Scan': {
            'L_TYPE': 'PyScript',
            'L_PATH': 'Scripts',
            'L_ITEM': 'sfc_scan.py',
            'L_ELEV': 'True',
            },
        'TDSSKiller': {
            'L_TYPE': 'Executable',
            'L_PATH': 'TDSSKiller',
            'L_ITEM': 'TDSSKiller.exe',
            'L_ARGS': (
                r' -l %log_dir%\TDSSKiller.log'
                r' -qpath %q_dir%'
                r' -accepteula'
                r' -accepteulaksn'
                r' -dcexact'
                r' -tdlfs'
                ),
            'Extra Code': [
                r'call "%bin%\Scripts\init_client_dir.cmd" /Quarantine',
                r'set "q_dir=%client_dir%\Quarantine\TDSSKiller"',
                r'mkdir "%q_dir%">nul 2>&1',
                ],
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
