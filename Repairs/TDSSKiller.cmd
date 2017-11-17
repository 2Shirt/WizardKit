@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CreateQuarantineDir
set "q_dir=%systemdrive%\WK\Quarantine\TDSSKiller"
mkdir "%q_dir%">nul 2>&1

:WKInfo
rem Create WK\Info\YYYY-MM-DD and set path as %log_dir%
call "%~dp0\..\.bin\Scripts\wk_info.cmd"

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "TDSSKiller.exe" "-l %log_dir%\TDSSKiller.log -qpath %q_dir% -accepteula -accepteulaksn -dcexact -tdlfs"
rem call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "TDSSKiller.exe" "-l %log_dir%\TDSSKiller.log -qpath %q_dir% -accepteula -accepteulaksn -dcexact -qsus -tdlfs"