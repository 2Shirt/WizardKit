@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:CreateQuarantineDir
set "q_dir=%systemdrive%\WK\Quarantine\KVRT"
mkdir "%q_dir%">nul 2>&1

:Launch
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin" "KVRT.exe" "-accepteula -d %q_dir% -processlevel 3 -dontcryptsupportinfo -fixednames"