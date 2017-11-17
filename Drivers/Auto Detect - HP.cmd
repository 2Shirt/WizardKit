@echo off

:Flags
for %%f in (%*) do (
    if /i "%%f" == "/DEBUG" (@echo on)
)

:Launch
echo Waiting for software installation to finish...
call "%~dp0\..\.bin\Scripts\Launch.cmd" Program "%~dp0\..\.bin\_Drivers" "HPSupportSolutionsFramework-12.3.11.29.exe" "" /admin /wait
start "" "http://h22213.www2.hp.com/ediags/gmd/ProdDetect.aspx?lc=en&cc=us"