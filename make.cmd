@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 creation tool
color 1b
pushd %~dp0
set "wd=%cd%"
set "winpe_ocs=%programfiles(x86)%\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs"


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

:Robocopy
del "%wd%\WK\Scripts\WK.log"
mkdir "%wd%\mount\WK"
robocopy /e "%wd%\WK" "%wd%\mount\WK"
mklink "%wd%\mount\System32\explorer.exe" "%wd%\mount\WK\Explorer++.exe"

:MenuLauncher
copy /y "%wd%\System32\menu.cmd" "%wd%\mount\Windows\System32\menu.cmd"

:ReplaceStartnet
copy /y "%wd%\System32\startnet.cmd" "%wd%\mount\Windows\System32\startnet.cmd"

:ReplaceNotepad
reg load HKLM\WinPE-SW mount\Windows\System32\config\SOFTWARE
reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v Debugger /t REG_SZ /d "X:\WK\Notepad2.exe /z" /f
reg unload HKLM\WinPE-SW

:Background
takeown /f "%wd%\mount\Windows\System32\winpe.jpg" /a
icacls "%wd%\mount\Windows\System32\winpe.jpg" /grant administrators:F
copy /y "%wd%\System32\winpe.jpg" "%wd%\mount\Windows\System32\winpe.jpg"

:ManualStuff
echo Now is the time to add stuff (optional).
echo.
echo Press any key to commit changes...
pause>nul

:Unmount
dism /unmount-image /mountdir:"%wd%\mount" /commit

:CreateISO
del winpe10-test.iso
makewinpemedia.cmd /iso "%wd%\pe_files" winpe10-test.iso
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