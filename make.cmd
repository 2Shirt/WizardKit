@echo off

:Init
setlocal EnableDelayedExpansion
title WinPE 10 creation tool
color 1b
pushd %~dp0

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:GetDate
:: Credit to SS64.com Code taken from http://ss64.com/nt/syntax-getdate.html
:: Use WMIC to retrieve date and time in ISO 8601 format.
FOR /F "skip=1 tokens=1-6" %%G IN ('WMIC Path Win32_LocalTime Get Day^,Hour^,Minute^,Month^,Second^,Year /Format:table') DO (
IF "%%~L"=="" goto s_done
    Set _yyyy=%%L
    Set _mm=00%%J
    Set _dd=00%%G
    Set _hour=00%%H
    SET _minute=00%%I
)
:s_done
:: Pad digits with leading zeros
Set _mm=%_mm:~-2%
Set _dd=%_dd:~-2%
Set _hour=%_hour:~-2%
Set _minute=%_minute:~-2%
Set iso_date=%_yyyy%-%_mm%-%_dd%

:Variables
set "wd=%cd%"
set "winpe_ocs=%programfiles(x86)%\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment"
set "pe_out=!wd!\pe_out"

:CheckForCleanup
echo Scanning for old build folders...
set "found_old="
if exist "!wd!\mount" (
    echo.  Found: "!wd!\mount"
    set "found_old=true"
)
if exist "!wd!\pe_files" (
    echo.  Found: "!wd!\pe_files"
    set "found_old=true"
)
if defined found_old (
    goto Cleanup
) else (
    echo.  No build folders found.
)
goto :BuildBoth

:Cleanup
echo.
choice /t 30 /c YN /d N /m "Delete the above folders?"
if %errorlevel% neq 1 goto Abort
rmdir /s /q "!wd!\mount"
rmdir /s /q "!wd!\pe_files"

:BuildBoth
for %%a in (amd64 x86) do (
    rem set vars
    set "arch=%%a"
    set "drivers=!wd!\Drivers\!arch!"
    set "mount=!wd!\mount\!arch!"
    set "pe_files=!wd!\pe_files\!arch!"
    set "winpe_ocs=%programfiles(x86)%\Windows Kits\10\Assessment and Deployment Kit\Windows Preinstallation Environment\!arch!\WinPE_OCs"
    
    rem Copy main files
    call copype.cmd !arch! "!pe_files!"
    rmdir /s /q "!pe_files!\media\bg-bg"
    rmdir /s /q "!pe_files!\media\cs-cz"
    rmdir /s /q "!pe_files!\media\da-dk"
    rmdir /s /q "!pe_files!\media\de-de"
    rmdir /s /q "!pe_files!\media\el-gr"
    rmdir /s /q "!pe_files!\media\en-gb"
    rmdir /s /q "!pe_files!\media\es-es"
    rmdir /s /q "!pe_files!\media\es-mx"
    rmdir /s /q "!pe_files!\media\et-ee"
    rmdir /s /q "!pe_files!\media\fi-fi"
    rmdir /s /q "!pe_files!\media\fr-ca"
    rmdir /s /q "!pe_files!\media\fr-fr"
    rmdir /s /q "!pe_files!\media\hr-hr"
    rmdir /s /q "!pe_files!\media\hu-hu"
    rmdir /s /q "!pe_files!\media\it-it"
    rmdir /s /q "!pe_files!\media\ja-jp"
    rmdir /s /q "!pe_files!\media\ko-kr"
    rmdir /s /q "!pe_files!\media\lt-lt"
    rmdir /s /q "!pe_files!\media\lv-lv"
    rmdir /s /q "!pe_files!\media\nb-no"
    rmdir /s /q "!pe_files!\media\nl-nl"
    rmdir /s /q "!pe_files!\media\pl-pl"
    rmdir /s /q "!pe_files!\media\pt-br"
    rmdir /s /q "!pe_files!\media\pt-pt"
    rmdir /s /q "!pe_files!\media\ro-ro"
    rmdir /s /q "!pe_files!\media\ru-ru"
    rmdir /s /q "!pe_files!\media\sk-sk"
    rmdir /s /q "!pe_files!\media\sl-si"
    rmdir /s /q "!pe_files!\media\sr-latn-cs"
    rmdir /s /q "!pe_files!\media\sr-latn-rs"
    rmdir /s /q "!pe_files!\media\sv-se"
    rmdir /s /q "!pe_files!\media\tr-tr"
    rmdir /s /q "!pe_files!\media\uk-ua"
    rmdir /s /q "!pe_files!\media\zh-cn"
    rmdir /s /q "!pe_files!\media\zh-hk"
    rmdir /s /q "!pe_files!\media\zh-tw"
    
    rem Mount Image
    mkdir "!mount!"
    dism /mount-image /imagefile:"!pe_files!\media\sources\boot.wim" /index:1 /mountdir:"!mount!" /logpath:"dism.log"
    
    rem Add Packages - More info: https://msdn.microsoft.com/en-us/library/windows/hardware/dn938382.aspx
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-EnhancedStorage.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-FMAPI.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-WMI.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-EnhancedStorage_en-us.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-WMI_en-us.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI before you install WinPE-NetFX.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-NetFx.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-NetFx_en-us.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI and WinPE-NetFX before you install WinPE-Scripting.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-Scripting.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-Scripting_en-us.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI, WinPE-NetFX, and WinPE-Scripting before you install WinPE-PowerShell.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-PowerShell.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-PowerShell_en-us.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-DismCmdlets.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-DismCmdlets.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-DismCmdlets_en-us.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-SecureBootCmdlets.cab" /logpath:"dism.log"

    rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-StorageWMI.
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-StorageWMI.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-StorageWMI_en-us.cab" /logpath:"dism.log"
    
    rem Add Drivers
    dism /add-driver /image:"!mount!" /driver:"!drivers!" /recurse /logpath:"dism.log"
    
    rem Force RamDisk size to try and avoid capture-image errors
    dism /image:"!mount!" /set-scratchspace:512
    
    rem Add WK Stuff
    del "!wd!\WK\Scripts\WK.log"
    mkdir "!mount!\WK"
    robocopy /s /r:3 /w:0 "!wd!\WK\!arch!" "!mount!\WK"
    mkdir "!mount!\WK\Scripts"
    robocopy /s /r:3 /w:0 "!wd!\Scripts" "!mount!\WK\Scripts"
    
    rem Add System32 Stuff
    copy /y "!wd!\System32\menu.cmd" "!mount!\Windows\System32\menu.cmd"
    copy /y "!wd!\System32\Winpeshl.ini" "!mount!\Windows\System32\Winpeshl.ini"
    
    rem   Background
    takeown /f "!mount!\Windows\System32\winpe.jpg" /a
    icacls "!mount!\Windows\System32\winpe.jpg" /grant administrators:F
    copy /y "!wd!\System32\winpe.jpg" "!mount!\Windows\System32\winpe.jpg"
    copy /y "!wd!\System32\winpe.jpg" "!mount!\WK\ConEmu\winpe.jpg"
    
    rem Registry Edits
    reg load HKLM\WinPE-SW "!mount!\Windows\System32\config\SOFTWARE"
    reg load HKLM\WinPE-SYS "!mount!\Windows\System32\config\SYSTEM"
    
    rem   Add 7-Zip to path
    reg add "HKLM\WinPE-SYS\ControlSet001\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%%SystemRoot%%\system32;%%SystemRoot%%;%%SystemRoot%%\System32\Wbem;%%SYSTEMROOT%%\System32\WindowsPowerShell\v1.0\;%%SystemDrive%%\WK\7-Zip" /f

    rem   Replace Notepad
    reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v Debugger /t REG_SZ /d "X:\WK\Notepad2\Notepad2-Mod.exe /z" /f

    rem   Unload registry hives
    reg unload HKLM\WinPE-SW
    reg unload HKLM\WinPE-SYS
    
    rem Unmount Image
    dism /unmount-image /mountdir:"!mount!" /commit
    
    rem Create ISO
    del "WinPE-!iso_date!-!arch!.iso"
    call makewinpemedia.cmd /iso "!pe_files!" "WinPE-!iso_date!-!arch!.iso"
)
goto Done

:Abort
color 4e
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