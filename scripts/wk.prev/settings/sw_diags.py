# Wizard Kit: Settings - SW Diagnostics

# General
AUTORUNS_SETTINGS = {
  r'Software\Sysinternals\AutoRuns': {
    'checkvirustotal': 1,
    'EulaAccepted': 1,
    'shownomicrosoft': 1,
    'shownowindows': 1,
    'showonlyvirustotal': 1,
    'submitvirustotal': 0,
    'verifysignatures': 1,
    },
  r'Software\Sysinternals\AutoRuns\SigCheck': {
    'EulaAccepted': 1,
    },
  r'Software\Sysinternals\AutoRuns\Streams': {
    'EulaAccepted': 1,
    },
  r'Software\Sysinternals\AutoRuns\VirusTotal': {
    'VirusTotalTermsAccepted': 1,
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
