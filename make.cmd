@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 creation tool
color 1b
pushd %~dp0
set "wd=%cd%"
set "winpe_ocs=%programfiles(x86)%\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs"
set "pe_iso=WinPE-2016-02d.iso"

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CopyPEFiles
call copype.cmd amd64 "%wd%\pe_files"

:Mount
rem echo Press any key to configure the WinPE image...
rem pause>nul
mkdir "%wd%\mount"
dism /mount-image /imagefile:"%wd%\pe_files\media\sources\boot.wim" /index:1 /mountdir:"%wd%\mount"

:AddPackages
mkdir "%wd%\log"

:: More info: https://msdn.microsoft.com/en-us/library/windows/hardware/dn938382(v=vs.85).aspx
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-FMAPI.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-WMI.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-WMI_en-us.cab" /logpath:"dism.log"

:: Install WinPE-WMI before you install WinPE-NetFX.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-NetFx.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-NetFx_en-us.cab" /logpath:"dism.log"

:: Install WinPE-WMI > WinPE-NetFX before you install WinPE-Scripting.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-Scripting.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-Scripting_en-us.cab" /logpath:"dism.log"

:: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting before you install WinPE-PowerShell.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-PowerShell.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-PowerShell_en-us.cab" /logpath:"dism.log"

:: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting > WinPE-PowerShell before you install WinPE-DismCmdlets.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-DismCmdlets.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-DismCmdlets_en-us.cab" /logpath:"dism.log"

:: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting > WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-SecureBootCmdlets.cab" /logpath:"dism.log"

:: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting > WinPE-PowerShell before you install WinPE-StorageWMI.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-StorageWMI.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-StorageWMI_en-us.cab" /logpath:"dism.log"

:: Install ?? before you install WinPE-EnhancedStorage.
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\WinPE-EnhancedStorage.cab" /logpath:"dism.log"
dism /add-package /image:"%wd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-EnhancedStorage_en-us.cab" /logpath:"dism.log"

:Robocopy
del "%wd%\WK\Scripts\WK.log"
mkdir "%wd%\mount\WK"
robocopy /e "%wd%\WK" "%wd%\mount\WK"
del "%wd%\mount\Windows\explorer.exe"
mklink /h "%wd%\mount\Windows\explorer.exe" "%wd%\mount\WK\Explorer++\Explorer++64.exe"

:System32Stuff
copy /y "%wd%\System32\menu.cmd" "%wd%\mount\Windows\System32\menu.cmd"
copy /y "%wd%\System32\Winpeshl.ini" "%wd%\mount\Windows\System32\Winpeshl.ini"

:RegistryEdits
reg load HKLM\WinPE-SW mount\Windows\System32\config\SOFTWARE
reg load HKLM\WinPE-SYS mount\Windows\System32\config\SYSTEM

rem Add 7-Zip to path
reg add "HKLM\WinPE-SYS\ControlSet001\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%%SystemRoot%%\system32;%%SystemRoot%%;%%SystemRoot%%\System32\Wbem;%%SYSTEMROOT%%\System32\WindowsPowerShell\v1.0\;%%SystemDrive%%\WK\7-Zip" /f

rem Replace Notepad
reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v Debugger /t REG_SZ /d "X:\WK\Notepad2\Notepad2-Mod64.exe /z" /f

rem Unload registry hives
reg unload HKLM\WinPE-SW
reg unload HKLM\WinPE-SYS

:Background
takeown /f "%wd%\mount\Windows\System32\winpe.jpg" /a
icacls "%wd%\mount\Windows\System32\winpe.jpg" /grant administrators:F
copy /y "%wd%\System32\winpe.jpg" "%wd%\mount\Windows\System32\winpe.jpg"
copy /y "%wd%\System32\winpe.jpg" "%wd%\mount\WK\ConEmu\winpe.jpg"

:ManualStuff
REM echo Now is the time to add stuff (optional).
REM echo.
REM echo Press any key to commit changes...
REM pause>nul

:Set-ScratchSpace
rem Force RamDisk size to try and avoid capture-image errors
dism /image:"%wd%\mount" /set-scratchspace:512

:Unmount
dism /unmount-image /mountdir:"%wd%\mount" /commit

:CreateISO
del "!pe_iso!"
makewinpemedia.cmd /iso "%wd%\pe_files" "!pe_iso!"
goto Done

:Abort
echo.
echo Aborted.
goto Exit

:Done
echo.
echo Done.
goto Exit

:Exit
echo.
echo Press any key to exit...
pause>nul
popd
color
endlocal