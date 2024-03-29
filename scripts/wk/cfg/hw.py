"""WizardKit: Config - Hardware"""
# pylint: disable=line-too-long
# vim: sts=2 sw=2 ts=2

import re

from collections import OrderedDict


# STATIC VARIABLES
ATTRIBUTE_COLORS = (
  # NOTE: Ordered by ascending importance
  ('Warning', 'YELLOW'),
  ('Error', 'RED'),
  ('Maximum', 'PURPLE'),
  )
# NOTE: Force 4K read block size for disks >= 3TB
BADBLOCKS_LARGE_DISK = 3 * 1024**4
CPU_CRITICAL_TEMP = 99
CPU_FAILURE_TEMP = 90
CPU_TEST_MINUTES = 7
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'
KNOWN_DISK_ATTRIBUTES = {
  # NVMe
  'critical_warning': {'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  'media_errors':     {'Blocking': False, 'Warning': None,  'Error': 1,     'Maximum': None,  },
  'power_on_hours':   {'Blocking': False, 'Warning': 17532, 'Error': 26298, 'Maximum': 100000,},
  'unsafe_shutdowns': {'Blocking': False, 'Warning': 1,     'Error': None,  'Maximum': None,  },
  # SMART
  5:     {'Hex': '05', 'Blocking': True,  'Warning': None,  'Error': 1,     'Maximum': None,  },
  9:     {'Hex': '09', 'Blocking': False, 'Warning': 17532, 'Error': 26298, 'Maximum': 100000,},
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
  r'MZ(7|N)LN(128|256|512|1T0)HA(HQ|JQ|LR)-000H(1|7)': {
    # Source: https://www.smartmontools.org/ticket/920
    201: {'Error': 99, 'PercentageLife': True, 'Note': '(PM871b thresholds)'},
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
SMC_IDS = {
  # Sources:  https://github.com/beltex/SMCKit/blob/master/SMCKit/SMC.swift
  #           http://www.opensource.apple.com/source/net_snmp/
  #           https://github.com/jedda/OSX-Monitoring-Tools
  'TA0P': {'CPU Temp': False, 'Source': 'Ambient'},
  'TA0S': {'CPU Temp': False, 'Source': 'PCIE Slot 1 Ambient'},
  'TA1P': {'CPU Temp': False, 'Source': 'Ambient'},
  'TA1S': {'CPU Temp': False, 'Source': 'PCIE Slot 1 PCB'},
  'TA2S': {'CPU Temp': False, 'Source': 'PCIE Slot 2 Ambient'},
  'TA3S': {'CPU Temp': False, 'Source': 'PCIE Slot 2 PCB'},
  'TC0C': {'CPU Temp': True,  'Source': 'CPU Core 1'},
  'TC0D': {'CPU Temp': True,  'Source': 'CPU Diode'},
  'TC0H': {'CPU Temp': True,  'Source': 'CPU Heatsink'},
  'TC0P': {'CPU Temp': True,  'Source': 'CPU Proximity'},
  'TC1C': {'CPU Temp': True,  'Source': 'CPU Core 2'},
  'TC1P': {'CPU Temp': True,  'Source': 'CPU Proximity 2'},
  'TC2C': {'CPU Temp': True,  'Source': 'CPU Core 3'},
  'TC2P': {'CPU Temp': True,  'Source': 'CPU Proximity 3'},
  'TC3C': {'CPU Temp': True,  'Source': 'CPU Core 4'},
  'TC3P': {'CPU Temp': True,  'Source': 'CPU Proximity 4'},
  'TCAC': {'CPU Temp': True,  'Source': 'CPU core from PCECI'},
  'TCAH': {'CPU Temp': True,  'Source': 'CPU HeatSink'},
  'TCBC': {'CPU Temp': True,  'Source': 'CPU B core from PCECI'},
  'TCBH': {'CPU Temp': True,  'Source': 'CPU HeatSink'},
  'Te1P': {'CPU Temp': False, 'Source': 'PCIE Ambient'},
  'Te1S': {'CPU Temp': False, 'Source': 'PCIE slot 1'},
  'Te2S': {'CPU Temp': False, 'Source': 'PCIE slot 2'},
  'Te3S': {'CPU Temp': False, 'Source': 'PCIE slot 3'},
  'Te4S': {'CPU Temp': False, 'Source': 'PCIE slot 4'},
  'TG0C': {'CPU Temp': False, 'Source': 'Mezzanine GPU Core'},
  'TG0P': {'CPU Temp': False, 'Source': 'Mezzanine GPU Exhaust'},
  'TH0P': {'CPU Temp': False, 'Source': 'Drive Bay 0'},
  'TH1P': {'CPU Temp': False, 'Source': 'Drive Bay 1'},
  'TH2P': {'CPU Temp': False, 'Source': 'Drive Bay 2'},
  'TH3P': {'CPU Temp': False, 'Source': 'Drive Bay 3'},
  'TH4P': {'CPU Temp': False, 'Source': 'Drive Bay 4'},
  'TM0P': {'CPU Temp': False, 'Source': 'CPU DIMM Exit Ambient'},
  'Tp0C': {'CPU Temp': False, 'Source': 'PSU1 Inlet Ambient'},
  'Tp0P': {'CPU Temp': False, 'Source': 'PSU1 Inlet Ambient'},
  'Tp1C': {'CPU Temp': False, 'Source': 'PSU1 Secondary Component'},
  'Tp1P': {'CPU Temp': False, 'Source': 'PSU1 Primary Component'},
  'Tp2P': {'CPU Temp': False, 'Source': 'PSU1 Secondary Component'},
  'Tp3P': {'CPU Temp': False, 'Source': 'PSU2 Inlet Ambient'},
  'Tp4P': {'CPU Temp': False, 'Source': 'PSU2 Primary Component'},
  'Tp5P': {'CPU Temp': False, 'Source': 'PSU2 Secondary Component'},
  'TS0C': {'CPU Temp': False, 'Source': 'CPU B DIMM Exit Ambient'},
  }
TEMP_COLORS = {
  float('-inf'):  'CYAN',
  00:             'BLUE',
  60:             'GREEN',
  70:             'YELLOW',
  80:             'ORANGE',
  90:             'RED',
  100:            'ORANGE_RED',
  }
TESTSTATION_FILE = '/run/archiso/bootmnt/teststation.name'
# THRESHOLDS: Rates used to determine HDD/SSD pass/fail
THRESH_HDD_MIN =       50 * 1024**2
THRESH_HDD_AVG_HIGH =  75 * 1024**2
THRESH_HDD_AVG_LOW =   65 * 1024**2
THRESH_SSD_MIN =       90 * 1024**2
THRESH_SSD_AVG_HIGH = 135 * 1024**2
THRESH_SSD_AVG_LOW =  100 * 1024**2
TMUX_SIDE_WIDTH = 20
TMUX_LAYOUT = OrderedDict({
  'Top':            {'height':  2,                'Check': True},
  'Started':        {'width':   TMUX_SIDE_WIDTH,  'Check': True},
  'Progress':       {'width':   TMUX_SIDE_WIDTH,  'Check': True},
  # Testing panes
  'Temps':          {'height':  1000,             'Check': False},
  'Prime95':        {'height':  11,               'Check': False},
  'SMART':          {'height':  4,                'Check': True},
  'badblocks':      {'height':  5,                'Check': True},
  'I/O Benchmark':  {'height':  1000,             'Check': False},
  })


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
