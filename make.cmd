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
    for %%t in (bg-bg cs-cz da-dk de-de el-gr en-gb es-es es-mx et-ee fi-fi fr-ca fr-fr hr-hr hu-hu it-it ja-jp ko-kr lt-lt lv-lv nb-no nl-nl pl-pl pt-br pt-pt ro-ro ru-ru sk-sk sl-si sr-latn-cs sr-latn-rs sv-se tr-tr uk-ua zh-cn zh-hk zh-tw) do (
        rmdir /s /q "!pe_files!\media\%%t"
        rmdir /s /q "!pe_files!\media\Boot\%%t"
        rmdir /s /q "!pe_files!\media\EFI\Microsoft\Boot\%%t"
    )
    
    rem Mount Image
    mkdir "!mount!"
    dism /mount-image /imagefile:"!pe_files!\media\sources\boot.wim" /index:1 /mountdir:"!mount!" /logpath:"dism.log"
    
    rem Add Packages - More info: https://msdn.microsoft.com/en-us/library/windows/hardware/dn938382.aspx
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-EnhancedStorage.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-FMAPI.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-WMI.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-EnhancedStorage_en-us.cab" /logpath:"dism.log"
    dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-WMI_en-us.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI before you install WinPE-NetFX.
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-NetFx.cab" /logpath:"dism.log"
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-NetFx_en-us.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI and WinPE-NetFX before you install WinPE-Scripting.
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-Scripting.cab" /logpath:"dism.log"
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-Scripting_en-us.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI, WinPE-NetFX, and WinPE-Scripting before you install WinPE-PowerShell.
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-PowerShell.cab" /logpath:"dism.log"
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-PowerShell_en-us.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-DismCmdlets.
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-DismCmdlets.cab" /logpath:"dism.log"
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-DismCmdlets_en-us.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-SecureBootCmdlets.
    rem rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-SecureBootCmdlets.cab" /logpath:"dism.log"

    rem rem   Install WinPE-WMI, WinPE-NetFX, WinPE-Scripting, and WinPE-PowerShell before you install WinPE-StorageWMI.
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\WinPE-StorageWMI.cab" /logpath:"dism.log"
    rem dism /add-package /image:"!mount!" /packagepath:"!winpe_ocs!\en-us\WinPE-StorageWMI_en-us.cab" /logpath:"dism.log"
    
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
    copy /y "!wd!\System32\Winpeshl.ini" "!mount!\Windows\System32\Winpeshl.ini"
    
    rem   Background
    takeown /f "!mount!\Windows\System32\winpe.jpg" /a
    icacls "!mount!\Windows\System32\winpe.jpg" /grant administrators:F
    copy /y "!wd!\System32\winpe.jpg" "!mount!\Windows\System32\winpe.jpg"
    copy /y "!wd!\System32\winpe.jpg" "!mount!\WK\conemu-maximus5\winpe.jpg"
    
    rem Registry Edits
    reg load HKLM\WinPE-SW "!mount!\Windows\System32\config\SOFTWARE"
    reg load HKLM\WinPE-SYS "!mount!\Windows\System32\config\SYSTEM"
    
    rem   Add 7-Zip and Python to path
    reg add "HKLM\WinPE-SYS\ControlSet001\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%%SystemRoot%%\system32;%%SystemRoot%%;%%SystemRoot%%\System32\Wbem;%%SYSTEMROOT%%\System32\WindowsPowerShell\v1.0\;%%SystemDrive%%\WK\7-Zip;%%SystemDrive%%\WK\python;%%SystemDrive%%\WK\wimlib" /f

    rem   Replace Notepad
    reg add "HKLM\WinPE-SW\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v Debugger /t REG_SZ /d "X:\WK\Notepad2\Notepad2-Mod.exe /z" /f

    rem   Unload registry hives
    reg unload HKLM\WinPE-SW
    reg unload HKLM\WinPE-SYS
    
    rem Unmount Image
    dism /unmount-image /mountdir:"!mount!" /commit
    
    rem Create ISO
    del "WinPE-!iso_date!-!arch!.iso"
    call makewinpemedia.cmd /iso "!pe_files!" "WinPE-!iso_date!-!arch!-testing.iso"
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