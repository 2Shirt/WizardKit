"""WizardKit: Config - Net"""
# pylint: disable=bad-whitespace
# vim: sts=2 sw=2 ts=2


# Servers
BACKUP_SERVERS = {
  'Server One': {
    'Address':  '10.0.0.10',
    'Share':    'Backups',
    'RO-User':  'restore',
    'RO-Pass':  'Abracadabra',
    'RW-User':  'backup',
    'RW-Pass':  'Abracadabra',
    },
  'Server Two': {
    'Address':  'servertwo.example.com',
    'Share':    'Backups',
    'RO-User':  'restore',
    'RO-Pass':  'Abracadabra',
    'RW-User':  'backup',
    'RW-Pass':  'Abracadabra',
    },
  }
CRASH_SERVER = {
  'Name':       'CrashServer',
  'Url':        '',
  'User':       '',
  'Pass':       '',
  'Headers':    {'X-Requested-With': 'XMLHttpRequest'},
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
