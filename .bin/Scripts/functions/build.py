# Wizard Kit: Functions - Build / Update

from functions.common import *

def download_file(out_dir, out_name, source_url):
    """Downloads a file using curl."""
    extract_item('curl', silent=True)
    _cmd = [
        global_vars['Tools']['curl'],
        # '-#LSfo', # ProgressBar
        '-Lfso',
        '{}/{}'.format(out_dir, out_name),
        source_url]
    os.makedirs(out_dir, exist_ok=True)
    run_program(_cmd, pipe=False)

def resolve_dynamic_url(source_url, regex):
    """Scan source_url for a url using the regex provided; returns str."""
    # Download the "download page"
    extract_item('curl', silent=True)
    _tmp_file = r'{TmpDir}\webpage.tmp'.format(**global_vars)
    _cmd = [
        global_vars['Tools']['curl'],
        '-#LSfo',
        _tmp_file,
        source_url]
    try:
        run_program(_cmd)
    except Exception:
        # "Fail silently as the download_file() function will catch it
        return None

    # Scan the file for the regex
    with open(_tmp_file, 'r') as file:
        for line in file:
            if re.search(regex, line):
                _url = line.strip()
                _url = re.sub(r'.*(a |)href="([^"]+)".*', r'\2', _url)
                _url = re.sub(r".*(a |)href='([^']+)'.*", r'\2', _url)
                break

    # Cleanup and return
    os.remove(_tmp_file)
    return _url

def update_adwcleaner():
    _path = global_vars['BinDir']
    _name = 'AdwCleaner.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/adwcleaner/dl/125/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/a/adwcleaner/AdwCleaner\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_eset():
    _path = global_vars['BinDir']
    _name = 'ESET.exe'
    _url = 'http://download.eset.com/special/eos/esetsmartinstaller_enu.exe'
    download_file(_path, _name, _url)

def update_jrt():
    _path = global_vars['BinDir']
    _name = 'JRT.exe'
    _url = 'http://downloads.malwarebytes.org/file/jrt'
    download_file(_path, _name, _url)

def update_kvrt():
    _path = global_vars['BinDir']
    _name = 'KVRT.exe'
    _url = 'http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe'
    download_file(_path, _name, _url)

def update_hitmanpro():
    _path = '{BinDir}/HitmanPro'.format(**global_vars)
    _name = 'HitmanPro.exe'
    _url = 'http://dl.surfright.nl/HitmanPro.exe'
    download_file(_path, _name, _url)

    _name = 'HitmanPro64.exe'
    _url = 'http://dl.surfright.nl/HitmanPro_x64.exe'
    download_file(_path, _name, _url)

def update_intel_driver_utility():
    _path = '{BinDir}/_Drivers'.format(**global_vars)
    _name = 'Intel Driver Update Utility.exe'
    _dl_page = 'http://www.intel.com/content/www/us/en/support/detect.html'
    _regex = r'a href.*http(s|)://downloadmirror\.intel\.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+/Intel%20Driver%20Update%20Utility%20Installer.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_intel_ssd_toolbox():
    _path = '{BinDir}/_Drivers'.format(**global_vars)
    _name = 'Intel SSD Toolbox.exe'
    _dl_page = 'https://downloadcenter.intel.com/download/26085/Intel-Solid-State-Drive-Toolbox'
    _regex = r'href=./downloads/eula/[0-9]+/Intel-Solid-State-Drive-Toolbox.httpDown=https\%3A\%2F\%2Fdownloadmirror\.intel\.com\%2F[0-9]+\%2Feng\%2FIntel\%20SSD\%20Toolbox\%20-\%20v[0-9\.]+.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = re.sub(r'.*httpDown=(.*)', r'\1', _url, re.IGNORECASE)
    _url = _url.replace('%3A', ':')
    _url = _url.replace('%2F', '/')
    download_file(_path, _name, _url)

def update_rkill():
    _path = '{BinDir}/RKill'.format(**global_vars)
    _name = 'RKill.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/rkill/dl/10/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/r/rkill/rkill\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_samsung_magician():
    print_warning('Disabled.')
    #~Broken~# _path = '{BinDir}/_Drivers'.format(**global_vars)
    #~Broken~# _name = 'Samsung Magician.zip'
    #~Broken~# _dl_page = 'http://www.samsung.com/semiconductor/minisite/ssd/download/tools.html'
    #~Broken~# _regex = r'href=./semiconductor/minisite/ssd/downloads/software/Samsung_Magician_Setup_v[0-9]+.zip'
    #~Broken~# _url = resolve_dynamic_url(_dl_page, _regex)
    #~Broken~# # Convert relative url to absolute
    #~Broken~# _url = 'http://www.samsung.com' + _url
    #~Broken~# download_file(_path, _name, _url)
    #~Broken~# # Extract and replace old copy
    #~Broken~# _args = [
    #~Broken~#     'e', '"{BinDir}/_Drivers/Samsung Magician.zip"'.format(**global_vars),
    #~Broken~#     '-aoa', '-bso0', '-bsp0',
    #~Broken~#     '-o"{BinDir}/_Drivers"'.format(**global_vars)
    #~Broken~# ]
    #~Broken~# run_program(seven_zip, _args)
    #~Broken~# try:
    #~Broken~#     os.remove('{BinDir}/_Drivers/Samsung Magician.zip'.format(**global_vars))
    #~Broken~#     #~PoSH~# Move-Item "$bin\_Drivers\Samsung*exe" "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null
    #~Broken~# except Exception:
    #~Broken~#     pass
    pass

def update_sysinternalssuite():
    _path = '{BinDir}/tmp'.format(**global_vars)
    _name = 'SysinternalsSuite.zip'
    _url = 'https://download.sysinternals.com/files/SysinternalsSuite.zip'
    download_file(_path, _name, _url)
    # Extract
    _args = [
        'e', '"{BinDir}/tmp/SysinternalsSuite.zip"'.format(**global_vars),
        '-aoa', '-bso0', '-bsp0',
        '-o"{BinDir}/SysinternalsSuite"'.format(**global_vars)]
    run_program(seven_zip, _args)
    try:
        os.remove('{BinDir}/tmp/SysinternalsSuite.zip'.format(**global_vars))
    except Exception:
        pass

def update_tdsskiller():
    _path = global_vars['BinDir']
    _name = 'TDSSKiller.exe'
    _url = 'http://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe'
    download_file(_path, _name, _url)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
