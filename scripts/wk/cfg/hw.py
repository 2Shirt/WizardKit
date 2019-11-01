"""WizardKit: Config - Hardware"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2


KNOWN_ATTRIBUTES = {
  # NVMe
  'critical_warning': {'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  'media_errors':     {'Blocking': False, 'Warning': None,  'Error': 1,     'Maximum': None,  },
  'power_on_hours':   {'Blocking': False, 'Warning': 17532, 'Error': 26298, 'Maximum': None,  },
  'unsafe_shutdowns': {'Blocking': False, 'Warning': 1,     'Error': None,  'Maximum': None,  },
  # SMART
  5:     {'Hex': '05', 'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  9:     {'Hex': '09', 'Blocking': False, 'Warning': 17532, 'Error': 26298, 'Maximum': None,  },
  10:    {'Hex': '10', 'Blocking': False, 'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  184:   {'Hex': 'B8', 'Blocking': False, 'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  187:   {'Hex': 'BB', 'Blocking': False, 'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  188:   {'Hex': 'BC', 'Blocking': False, 'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  196:   {'Hex': 'C4', 'Blocking': False, 'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  197:   {'Hex': 'C5', 'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  198:   {'Hex': 'C6', 'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  199:   {'Hex': 'C7', 'Blocking': False, 'Warning': None,  'Error': 1,     'Maximum': None,  },
  201:   {'Hex': 'C9', 'Blocking': False, 'Warning': None,  'Error': 1,     'Maximum': 10000, },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
