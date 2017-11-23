# Wizard Kit: Functions - Product Keys

from functions.common import *

# Regex
REGEX_REGISTRY_DIRS = re.compile(
    r'^(config$|RegBack$|System32$|Transfer|Win)',
    re.IGNORECASE)
REGEX_SOFTWARE_HIVE = re.compile(r'^Software$', re.IGNORECASE)

def extract_keys():
    """Extract keys from provided hives and return a dict."""
    keys = {}

    # Extract keys
    extract_item('ProduKey', silent=True)
    for hive in find_software_hives():
        cmd = [
            global_vars['Tools']['ProduKey'],
            '/IEKeys', '0',
            '/WindowsKeys', '1',
            '/OfficeKeys', '1',
            '/ExtractEdition', '1',
            '/nosavereg',
            '/regfile', hive,
            '/scomma', '']
        try:
            out = run_program(cmd)
        except subprocess.CalledProcessError:
            # Ignore and return empty dict
            pass
        else:
            for line in out.stdout.decode().splitlines():
                # Add key to keys under product only if unique
                tmp = line.split(',')
                product = tmp[0]
                key = tmp[2]
                if product not in keys:
                    keys[product] = []
                if key not in keys[product]:
                    keys[product].append(key)
    
    # Done
    return keys

def list_clientdir_keys():
    """List product keys found in hives inside the ClientDir."""
    keys = extract_keys()
    key_list = []
    if keys:
        for product in sorted(keys):
            key_list.append(product)
            for key in sorted(keys[product]):
                key_list.append('    {key}'.format(key=key))
    else:
        key_list.append('No keys found.')

    return key_list

def find_software_hives():
    """Search for transferred SW hives and return a list."""
    hives = []
    search_paths = [global_vars['ClientDir']]

    while len(search_paths) > 0:
        for item in os.scandir(search_paths.pop(0)):
            if item.is_dir() and REGEX_REGISTRY_DIRS.search(item.name):
                search_paths.append(item.path)
            if item.is_file() and REGEX_SOFTWARE_HIVE.search(item.name):
                hives.append(item.path)

    return hives

def get_product_keys():
    """List product keys from saved report."""
    keys = []
    log_file = r'{LogDir}\Product Keys (ProduKey).txt'.format(**global_vars)
    with open (log_file, 'r') as f:
        for line in f.readlines():
            if re.search(r'^Product Name', line):
                line = re.sub(r'^Product Name\s+:\s+(.*)', r'\1', line.strip())
                keys.append(line)

    if keys:
        return keys
    else:
        return ['No product keys found']

def run_produkey():
    """Run ProduKey and save report in the ClientDir."""
    extract_item('ProduKey', silent=True)
    log_file = r'{LogDir}\Product Keys (ProduKey).txt'.format(**global_vars)
    if not os.path.exists(log_file):
        # Clear current configuration
        for config in ['ProduKey.cfg', 'ProduKey64.cfg']:
            config = r'{BinDir}\ProduKey\{config}'.format(
                config=config, **global_vars)
            try:
                if os.path.exists(config):
                    os.remove(config)
            except Exception:
                pass
        cmd = [
            global_vars['Tools']['ProduKey'],
            '/nosavereg',
            '/stext',
            log_file]
        run_program(cmd, check=False)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
