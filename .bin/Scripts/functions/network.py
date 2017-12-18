#!/bin/python3
#
## Wizard Kit: Functions - Network

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.common import *

# REGEX
REGEX_VALID_IP = re.compile(
    r'(10.\d+.\d+.\d+'
    r'|172.(1[6-9]|2\d|3[0-1])'
    r'|192.168.\d+.\d+)',
    re.IGNORECASE)

def connect_to_network():
    """Connect to network if not already connected."""
    net_ifs = psutil.net_if_addrs()
    net_ifs = [i[:2] for i in net_ifs.keys()]

    # Bail if currently connected
    if is_connected():
        return
    
    # LAN
    if 'en' in net_ifs:
        # Reload the tg3/broadcom driver (known fix for some Dell systems)
        try_and_print(message='Reloading drivers...', function=reload_tg3)
    
    # WiFi
    if not is_connected() and 'wl' in net_ifs:
        cmd = [
            'nmcli', 'dev', 'wifi',
            'connect', WIFI_SSID,
            'password', WIFI_PASSWORD]
        try_and_print(
            message = 'Connecting to {}...'.format(WIFI_SSID),
            function = run_program,
            cmd = cmd)

def is_connected():
    """Check for a valid private IP."""
    devs = psutil.net_if_addrs()
    for dev in devs.values():
        for family in dev:
            if REGEX_VALID_IP.search(family.address):
                # Valid IP found
                return True
    # Else
    return False

def reload_tg3():
    """Reload tg3 module as a workaround for some Dell systems."""
    run_program(['sudo', 'modprobe', '-r', 'tg3'])
    run_program(['sudo', 'modprobe', 'broadcom'])
    run_program(['sudo', 'modprobe', 'tg3'])
    sleep(5)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

