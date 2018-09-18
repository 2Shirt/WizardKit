#!/bin/python3
#
## Wizard Kit: Functions - Network

import os
import shutil
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
    
    # WiFi
    if 'wl' in net_ifs:
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

def show_valid_addresses():
    """Show all valid private IP addresses assigned to the system."""
    devs = psutil.net_if_addrs()
    for dev, families in sorted(devs.items()):
        for family in families:
            if REGEX_VALID_IP.search(family.address):
                # Valid IP found
                show_data(message=dev, data=family.address)

def speedtest():
    """Run a network speedtest using speedtest-cli."""
    result = run_program(['speedtest-cli', '--simple'])
    output = [line.strip() for line in result.stdout.decode().splitlines()
        if line.strip()]
    output = [line.split() for line in output]
    output = [(a, float(b), c) for a, b, c in output]
    return ['{:10}{:6.2f} {}'.format(*line) for line in output]

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

