#!/bin/bash

cd ../../
mkdir Installers/Extras/Office -p
pushd Installers/Extras/Office
mkdir 2007
mkdir 2010
mkdir 2013
mkdir 2016

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/2007 Microsoft Office system (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/2007 Microsoft Office system (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/2007 Microsoft Office system (SP3).cmd"
sed -ir 's/__ITEM__/2007 Microsoft Office system (SP3)/' "2007/2007 Microsoft Office system (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Access 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Access 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Access 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Access 2007 (SP3)/' "2007/Access 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/AccessRuntime2007.cmd"
sed -ir 's/__TYPE__/Office/' "2007/AccessRuntime2007.cmd"
sed -ir 's/__PATH__/2007/' "2007/AccessRuntime2007.cmd"
sed -ir 's/__ITEM__/AccessRuntime2007.exe/' "2007/AccessRuntime2007.cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Home and Student 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Home and Student 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Home and Student 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Home and Student 2007 (SP3)/' "2007/Home and Student 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Outlook 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Outlook 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Outlook 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Outlook 2007 (SP3)/' "2007/Outlook 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Professional 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Professional 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Professional 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Professional 2007 (SP3)/' "2007/Professional 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Publisher 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Publisher 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Publisher 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Publisher 2007 (SP3)/' "2007/Publisher 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2007/Small Business 2007 (SP3).cmd"
sed -ir 's/__TYPE__/Office/' "2007/Small Business 2007 (SP3).cmd"
sed -ir 's/__PATH__/2007/' "2007/Small Business 2007 (SP3).cmd"
sed -ir 's/__ITEM__/Small Business 2007 (SP3)/' "2007/Small Business 2007 (SP3).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2010/Outlook 2010 (SP2) (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2010/Outlook 2010 (SP2) (x32).cmd"
sed -ir 's/__PATH__/2010/' "2010/Outlook 2010 (SP2) (x32).cmd"
sed -ir 's/__ITEM__/Outlook 2010 (SP2) (x32)/' "2010/Outlook 2010 (SP2) (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2010/Outlook 2010 (SP2) (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2010/Outlook 2010 (SP2) (x64).cmd"
sed -ir 's/__PATH__/2010/' "2010/Outlook 2010 (SP2) (x64).cmd"
sed -ir 's/__ITEM__/Outlook 2010 (SP2) (x64)/' "2010/Outlook 2010 (SP2) (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2010/Professional Plus 2010 (SP2).cmd"
sed -ir 's/__TYPE__/Office/' "2010/Professional Plus 2010 (SP2).cmd"
sed -ir 's/__PATH__/2010/' "2010/Professional Plus 2010 (SP2).cmd"
sed -ir 's/__ITEM__/Professional Plus 2010 (SP2)/' "2010/Professional Plus 2010 (SP2).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2010/Publisher 2010 (SP2).cmd"
sed -ir 's/__TYPE__/Office/' "2010/Publisher 2010 (SP2).cmd"
sed -ir 's/__PATH__/2010/' "2010/Publisher 2010 (SP2).cmd"
sed -ir 's/__ITEM__/Publisher 2010 (SP2)/' "2010/Publisher 2010 (SP2).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2010/Single Image 2010 (SP2).cmd"
sed -ir 's/__TYPE__/Office/' "2010/Single Image 2010 (SP2).cmd"
sed -ir 's/__PATH__/2010/' "2010/Single Image 2010 (SP2).cmd"
sed -ir 's/__ITEM__/Single Image 2010 (SP2)/' "2010/Single Image 2010 (SP2).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Home and Business 2013 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Home and Business 2013 (x64).cmd"
sed -ir 's/__PATH__/2013/' "2013/Home and Business 2013 (x64).cmd"
sed -ir 's/__ITEM__/hb_64.xml/' "2013/Home and Business 2013 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Home and Student 2013 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Home and Student 2013 (x64).cmd"
sed -ir 's/__PATH__/2013/' "2013/Home and Student 2013 (x64).cmd"
sed -ir 's/__ITEM__/hs_64.xml/' "2013/Home and Student 2013 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Office 365 2013 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Office 365 2013 (x64).cmd"
sed -ir 's/__PATH__/2013/' "2013/Office 365 2013 (x64).cmd"
sed -ir 's/__ITEM__/365_64.xml/' "2013/Office 365 2013 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Home and Business 2013 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Home and Business 2013 (x32).cmd"
sed -ir 's/__PATH__/2013/' "2013/Home and Business 2013 (x32).cmd"
sed -ir 's/__ITEM__/hb_32.xml/' "2013/Home and Business 2013 (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Home and Student 2013 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Home and Student 2013 (x32).cmd"
sed -ir 's/__PATH__/2013/' "2013/Home and Student 2013 (x32).cmd"
sed -ir 's/__ITEM__/hs_32.xml/' "2013/Home and Student 2013 (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2013/Office 365 2013 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2013/Office 365 2013 (x32).cmd"
sed -ir 's/__PATH__/2013/' "2013/Office 365 2013 (x32).cmd"
sed -ir 's/__ITEM__/365_32.xml/' "2013/Office 365 2013 (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Home and Business 2016 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Home and Business 2016 (x64).cmd"
sed -ir 's/__PATH__/2016/' "2016/Home and Business 2016 (x64).cmd"
sed -ir 's/__ITEM__/hb_64.xml/' "2016/Home and Business 2016 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Home and Student 2016 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Home and Student 2016 (x64).cmd"
sed -ir 's/__PATH__/2016/' "2016/Home and Student 2016 (x64).cmd"
sed -ir 's/__ITEM__/hs_64.xml/' "2016/Home and Student 2016 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Office 365 2016 (x64).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Office 365 2016 (x64).cmd"
sed -ir 's/__PATH__/2016/' "2016/Office 365 2016 (x64).cmd"
sed -ir 's/__ITEM__/365_64.xml/' "2016/Office 365 2016 (x64).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Home and Business 2016 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Home and Business 2016 (x32).cmd"
sed -ir 's/__PATH__/2016/' "2016/Home and Business 2016 (x32).cmd"
sed -ir 's/__ITEM__/hb_32.xml/' "2016/Home and Business 2016 (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Home and Student 2016 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Home and Student 2016 (x32).cmd"
sed -ir 's/__PATH__/2016/' "2016/Home and Student 2016 (x32).cmd"
sed -ir 's/__ITEM__/hs_32.xml/' "2016/Home and Student 2016 (x32).cmd"

cp ../../../.bin/Scripts/Launcher_Template.cmd "2016/Office 365 2016 (x32).cmd"
sed -ir 's/__TYPE__/Office/' "2016/Office 365 2016 (x32).cmd"
sed -ir 's/__PATH__/2016/' "2016/Office 365 2016 (x32).cmd"
sed -ir 's/__ITEM__/365_32.xml/' "2016/Office 365 2016 (x32).cmd"
popd