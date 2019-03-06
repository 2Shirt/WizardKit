# Wizard Kit: Settings - Information

# General
REG_PROFILE_LIST = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'
REG_SHELL_FOLDERS = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
TMP_HIVE_PATH = 'TEMP_HIVE_MOUNT'
EXTRA_FOLDERS = [
  'Dropbox',
  'Google Drive',
  'OneDrive',
  'SkyDrive',
]
SHELL_FOLDERS = {
  #GUIDs from: https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx
  'Desktop': (
    '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}',
    ),
  'Documents': (
    'Personal',
    '{FDD39AD0-238F-46AF-ADB4-6C85480369C7}',
    ),
  'Downloads': (
    '{374DE290-123F-4565-9164-39C4925E467B}',
    ),
  'Favorites': (
    '{1777F761-68AD-4D8A-87BD-30B759FA33DD}',
    ),
  'Music': (
    'My Music',
    '{4BD8D571-6D19-48D3-BE97-422220080E43}',
    ),
  'Pictures': (
    'My Pictures',
    '{33E28130-4E1E-4676-835A-98395C3BC3BB}',
    ),
  'Videos': (
    'My Video',
    '{18989B1D-99B5-455B-841C-AB7C74E4DDFC}',
    ),
}

# Regex
REGEX_OFFICE = re.compile(
  r'(Microsoft (Office\s+'
    r'(365|Enterprise|Home|Pro(\s|fessional)'
    r'|Single|Small|Standard|Starter|Ultimate|system)'
    r'|Works[-\s\d]+\d)'
  r'|(Libre|Open|Star)\s*Office'
  r'|WordPerfect|Gnumeric|Abiword)',
  re.IGNORECASE)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
