"""WizardKit: Config - Hardware"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2

import re


# STATIC VARIABLES
ATTRIBUTE_COLORS = (
  # NOTE: Ordered by ascending importance
  ('Warning', 'YELLOW'),
  ('Error', 'RED'),
  ('Maximum', 'PURPLE'),
  )
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'
KNOWN_DISK_ATTRIBUTES = {
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
KNOWN_DISK_MODELS = {
  # model_regex: model_attributes
  r'CT(250|500|1000|2000)MX500SSD(1|4)': {
    197: {'Warning': 1, 'Error': 2, 'Note': '(MX500 thresholds)',},
    },
  }
KNOWN_RAM_VENDOR_IDS = {
  # https://github.com/hewigovens/hewigovens.github.com/wiki/Memory-vendor-code
  '0x014F': 'Transcend',
  '0x2C00': 'Micron',
  '0x802C': 'Micron',
  '0x80AD': 'Hynix',
  '0x80CE': 'Samsung',
  '0xAD00': 'Hynix',
  '0xCE00': 'Samsung',
  }
REGEX_POWER_ON_TIME = re.compile(
  r'^(\d+)([Hh].*|\s+\(\d+\s+\d+\s+\d+\).*)'
  )


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
