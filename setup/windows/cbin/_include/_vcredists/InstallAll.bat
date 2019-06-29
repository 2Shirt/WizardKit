@echo off
setlocal

start "" /wait "2010\x32\vcredist.exe" /passive /norestart
start "" /wait "2010\x64\vcredist.exe" /passive /norestart

start "" /wait "2012u4\x32\vcredist.exe" /passive /norestart
start "" /wait "2012u4\x64\vcredist.exe" /passive /norestart

start "" /wait "2013\x32\vcredist.exe" /install /passive /norestart
start "" /wait "2013\x64\vcredist.exe" /install /passive /norestart

start "" /wait "2015u3\x32\vcredist.exe" /install /passive /norestart
start "" /wait "2015u3\x64\vcredist.exe" /install /passive /norestart

start "" /wait "2017\x32\vcredist.exe" /install /passive /norestart
start "" /wait "2017\x64\vcredist.exe" /install /passive /norestart

endlocal
