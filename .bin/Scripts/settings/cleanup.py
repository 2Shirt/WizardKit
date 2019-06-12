'''Wizard Kit: Settings - Cleanup'''
# vim: sts=2 sw=2 ts=2

import re

# Regex
DESKTOP_ITEMS = re.compile(
  r'^(JRT|RKill|sc-cleaner)',
  re.IGNORECASE,
  )

# Registry
UAC_DEFAULTS_WIN7 = {
  r'Software\Microsoft\Windows\CurrentVersion\Policies\System': {
    'DWORD Items': {
      'ConsentPromptBehaviorAdmin': 5,
      'EnableLUA': 1,
      'PromptOnSecureDesktop': 1,
      },
    },
  }
UAC_DEFAULTS_WIN10 = {
  r'Software\Microsoft\Windows\CurrentVersion\Policies\System': {
    'DWORD Items': {
      'ConsentPromptBehaviorAdmin': 5,
      'ConsentPromptBehaviorUser': 3,
      'EnableInstallerDetection': 1,
      'EnableLUA': 1,
      'EnableVirtualization': 1,
      'PromptOnSecureDesktop': 1,
      },
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
