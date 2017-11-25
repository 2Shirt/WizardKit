@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 update tool
color 1b
pushd %~dp0
set "winpe_ocs=%programfiles(x86)%\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\amd64\WinPE_OCs"


:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CopyPEFiles
rem call copype.cmd amd64 "%cd%\wd"

:Mount
rem echo Press any key to configure the WinPE image...
rem pause>nul
mkdir "%cd%\mount"
dism /mount-image /imagefile:"%cd%\wd\media\sources\boot.wim" /index:1 /mountdir:"%cd%\mount"

:AddPackages
rem :: More info: https://msdn.microsoft.com/en-us/library/windows/hardware/dn938382(v=vs.85).aspx
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-FMAPI.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-WMI.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-WMI_en-us.cab"

rem :: Install WinPE-WMI before you install WinPE-NetFX.
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-NetFx.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-NetFx_en-us.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-Scripting.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-Scripting_en-us.cab"

rem :: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting before you install WinPE-PowerShell.
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-PowerShell.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-PowerShell_en-us.cab"

rem :: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting > WinPE-PowerShell before you install WinPE-DismCmdlets.
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-DismCmdlets.cab"
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\en-us\WinPE-DismCmdlets_en-us.cab"

rem :: Install WinPE-WMI > WinPE-NetFX > WinPE-Scripting > WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
rem dism /add-package /image:"%cd%\mount" /packagepath:"%winpe_ocs%\WinPE-SecureBootCmdlets.cab"

:Robocopy
del "%cd%\WK\Scripts\WK.log"
rem mkdir "%cd%\mount\WK"
robocopy /e "%cd%\WK" "%cd%\mount\WK"

:MenuLauncher
copy /y "%cd%\System32\menu.cmd" "%cd%\mount\Windows\System32\menu.cmd"

:ReplaceStartnet
copy /y "%cd%\System32\startnet.cmd" "%cd%\mount\Windows\System32\startnet.cmd"

:ReplaceNotepad
reg load HKLM\WinPE-SW mount\Windows\System32\config\SOFTWARE
reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v Debugger /t REG_SZ /d "X:\WK\Notepad2.exe /z" /f
reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\explorer.exe" /v Debugger /t REG_SZ /d "X:\WK\Explorer++.exe /z" /f
reg unload HKLM\WinPE-SW

:Background
takeown /f "%cd%\mount\Windows\System32\winpe.jpg" /a
icacls "%cd%\mount\Windows\System32\winpe.jpg" /grant administrators:F
copy /y "%cd%\System32\winpe.jpg" "%cd%\mount\Windows\System32\winpe.jpg"

:ManualStuff
echo Now is the time to add stuff (optional).
echo.
echo Press any key to commit changes...
pause>nul

:Unmount
dism /unmount-image /mountdir:"%cd%\mount" /commit

:CreateISO
del winpe10-test.iso
makewinpemedia.cmd /iso wd winpe10-test.iso
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