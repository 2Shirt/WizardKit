"""WizardKit: Config - Hardware"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2


ATTRIBUTES = {
  # NVMe
  'critical_warning': {'Critical': True,  'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,   },
  'media_errors':     {'Critical': False, 'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,   },
  'power_on_hours':   {'Critical': False, 'Ignore': True,   'Warning': 17532, 'Error': 26298, 'Maximum': None,   },
  'unsafe_shutdowns': {'Critical': False, 'Ignore': True,   'Warning': 1,     'Error': None,  'Maximum': None,   },
  # SMART
  5:     {'Hex': '05', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  9:     {'Hex': '09', 'Critical': False,  'Ignore': True,   'Warning': 17532, 'Error': 26298, 'Maximum': None,  },
  10:    {'Hex': '10', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  184:   {'Hex': 'B8', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  187:   {'Hex': 'BB', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  188:   {'Hex': 'BC', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  196:   {'Hex': 'C4', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
  197:   {'Hex': 'C5', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  198:   {'Hex': 'C6', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  199:   {'Hex': 'C7', 'Critical': False,  'Ignore': True,   'Warning': None,  'Error': 1,     'Maximum': None,  },
  201:   {'Hex': 'C9', 'Critical': False,  'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': 10000, },
  }
ATTRIBUTE_COLORS = (
  # NOTE: Ordered by ascending importance
  ('Warning', 'YELLOW'),
  ('Error', 'RED'),
  ('Maximum', 'PURPLE'),
  )


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
