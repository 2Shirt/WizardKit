@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as %log_dir%
call "%~dp0\..\.bin\Scripts\wk_info.cmd"

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\FastCopy" "FastCopy.exe" "/logfile=%log_dir%\FastCopy.log /cmd=noexist_only /utf8 /skip_empty_dir /linkdest /exclude=$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db /to=%systemdrive%\WK\Transfer\" /admin