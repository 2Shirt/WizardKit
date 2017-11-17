# Wizard Kit: Functions - Activation

import subprocess

from borrowed import acpi
from os import environ

# Variables
SLMGR = r'{}\System32\slmgr.vbs'.format(environ.get('SYSTEMROOT'))

# Error Classes
class BIOSKeyNotFoundError(Exception):
    pass

def activate_windows_with_bios():
    """Attempt to activate Windows with a key stored in the BIOS."""
    # Code borrowed from https://github.com/aeruder/get_win8key
    #####################################################
    #script to query windows 8.x OEM key from PC firmware
    #ACPI -> table MSDM -> raw content -> byte offset 56 to end
    #ck, 03-Jan-2014 (christian@korneck.de)
    #####################################################
    bios_key = None
    table = b"MSDM"
    if acpi.FindAcpiTable(table) is True:
        rawtable = acpi.GetAcpiTable(table)
        #http://msdn.microsoft.com/library/windows/hardware/hh673514
        #byte offset 36 from beginning \
        #   = Microsoft 'software licensing data structure' \
        #   / 36 + 20 bytes offset from beginning = Win Key
        bios_key = rawtable[56:len(rawtable)].decode("utf-8")
    else:
        raise Exception('ACPI table {} not found.'.format(str(table)))
    if bios_key is None:
        raise BIOSKeyNotFoundError

    # Install Key
    cmd = ['cscript', '//nologo', SLMGR, '/ipk', bios_key]
    subprocess.run(cmd, check=False)
    sleep(5)

    # Attempt activation
    cmd = ['cscript', '//nologo', SLMGR, '/ato']
    subprocess.run(cmd, check=False)
    sleep(5)

    # Check status
    if not windows_is_activated():
        raise Exception('Activation Failed')

def get_activation_string():
    """Get activation status, returns str."""
    act_str = subprocess.run(
        ['cscript', '//nologo', SLMGR, '/xpr'], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    act_str = act_str.stdout.decode()
    act_str = act_str.splitlines()
    act_str = act_str[1].strip()
    return act_str

def windows_is_activated():
    """Check if Windows is activated via slmgr.vbs and return bool."""
    activation_string = subprocess.run(
        ['cscript', '//nologo', SLMGR, '/xpr'], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    activation_string = activation_string.stdout.decode()
    
    return bool(activation_string and 'permanent' in activation_string)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
