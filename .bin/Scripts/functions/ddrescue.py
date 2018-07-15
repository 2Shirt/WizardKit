# Wizard Kit: Functions - ddrescue

import json
import re

from functions.common import *

# STATIC VARIABLES
USAGE="""    {script_name} clone [source [destination]]
    {script_name} image [source [destination]]
    (e.g. {script_name} clone /dev/sda /dev/sdb)
"""

# Functions
def menu_clone(source_path, dest_path):
    print_success('GNU ddrescue: Cloning Menu')
    pass

def menu_ddrescue(*args):
    """Main ddrescue loop/menu."""
    args = list(args)
    script_name = os.path.basename(args.pop(0))
    run_mode = ''
    source_path = None
    dest_path = None

    # Parse args
    try:
        run_mode = args.pop(0)
        source_path = args.pop(0)
        dest_path = args.pop(0)
    except IndexError:
        # We'll set the missing paths later
        pass

    # Show proper menu or exit
    if run_mode == 'clone':
        menu_clone(source_path, dest_path)
    elif run_mode == 'image':
        menu_image(source_path, dest_path)
    else:
        if not re.search(r'(^$|help|-h|\?)', run_mode, re.IGNORECASE):
            print_error('Invalid mode.')
        show_usage(script_name)
        exit_script()

def menu_image(source_path, dest_path):
    print_success('GNU ddrescue: Imaging Menu')
    pass

def show_usage(script_name):
    print_info('Usage:')
    print_standard(USAGE.format(script_name=script_name))

if __name__ == '__main__':
    print("This file is not meant to be called directly.")

# vim: sts=4 sw=4 ts=4
