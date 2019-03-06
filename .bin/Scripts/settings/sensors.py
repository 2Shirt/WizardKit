# Wizard Kit: Settings - Sensors

import re

# General
TEMP_LIMITS = {
  'GREEN':  60,
  'YELLOW': 70,
  'ORANGE': 80,
  'RED':    90,
  }


# Regex
REGEX_COLORS = re.compile(r'\033\[\d+;?1?m')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
