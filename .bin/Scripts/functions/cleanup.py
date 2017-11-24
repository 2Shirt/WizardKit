# Wizard Kit: Functions - Cleanup

from functions.common import *

def cleanup_adwcleaner():
    """Move AdwCleaner folders into the ClientDir."""
    source_path = r'{SYSTEMDRIVE}\AdwCleaner'.format(**global_vars['Env'])
    source_quarantine = r'{}\Quarantine'.format(source_path)
    
    # Quarantine
    if os.path.exists(source_quarantine):
        os.makedirs(global_vars['QuarantineDir'], exist_ok=True)
        dest_name = r'{QuarantineDir}\AdwCleaner_{Date-Time}'.format(
            **global_vars)
        dest_name = non_clobber_rename(dest_name)
        shutil.move(source_quarantine, dest_name)
    
    # Delete source folder if empty
    try:
        os.rmdir(source_path)
    except OSError:
        pass
    
    # Main folder
    if os.path.exists(source_path):
        os.makedirs(global_vars['ProgBackupDir'], exist_ok=True)
        dest_name = r'{ProgBackupDir}\AdwCleaner_{Date-Time}'.format(
            **global_vars)
        dest_name = non_clobber_rename(dest_name)
        shutil.move(source_path, dest_name)

def cleanup_cbs(dest_folder):
    """Safely cleanup a known CBS archive bug under Windows 7.
    
    If a CbsPersist file is larger than 2 Gb then the auto archive feature
    continually fails and will fill up the system drive with temp files.
    
    This function moves the temp files and CbsPersist file to a temp folder,
    compresses the CbsPersist files with 7-Zip, and then opens the temp folder
    for the user to manually save the backup files and delete the temp files.
    """
    backup_folder = r'{dest_folder}\CbsFix'.format(dest_folder=dest_folder)
    temp_folder = r'{backup_folder}\Temp'.format(backup_folder=backup_folder)
    os.makedirs(backup_folder, exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)
    
    # Move files into temp folder
    cbs_path = r'{SYSTEMROOT}\Logs\CBS'.format(**global_vars['Env'])
    for entry in os.scandir(cbs_path):
        # CbsPersist files
        if entry.name.lower().startswith('cbspersist'):
            dest_name = r'{}\{}'.format(temp_folder, entry.name)
            dest_name = non_clobber_rename(dest_name)
            shutil.move(entry.path, dest_name)
    temp_path = r'{SYSTEMROOT}\Temp'.format(**global_vars['Env'])
    for entry in os.scandir(temp_path):
        # cab_ files
        if entry.name.lower().startswith('cab_'):
            dest_name = r'{}\{}'.format(temp_folder, entry.name)
            dest_name = non_clobber_rename(dest_name)
            shutil.move(entry.path, dest_name)
    
    # Compress CbsPersist files with 7-Zip
    cmd = [
        global_vars['Tools']['SevenZip'],
        'a', '-t7z', '-mx=3', '-bso0', '-bse0',
        r'{}\CbsPersists.7z'.format(backup_folder),
        r'{}\CbsPersist*'.format(temp_folder)]
    run_program(cmd)

def cleanup_desktop():
    """Move known backup files and reports into the ClientDir."""
    dest_folder = r'{ProgBackupDir}\Desktop_{Date-Time}'.format(**global_vars)
    os.makedirs(dest_folder, exist_ok=True)
    
    desktop_path = r'{USERPROFILE}\Desktop'.format(**global_vars['Env'])
    for entry in os.scandir(desktop_path):
        # JRT, RKill, Shortcut cleaner
        if re.search(r'^(JRT|RKill|sc-cleaner)', entry.name, re.IGNORECASE):
            dest_name = r'{}\{}'.format(dest_folder, entry.name)
            dest_name = non_clobber_rename(dest_name)
            shutil.move(entry.path, dest_name)
    
    # Remove dir if empty
    try:
        os.rmdir(dest_folder)
    except OSError:
        pass

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
