"""WizardKit: Config - Main

NOTE: Non-standard formating is used for BASH/BATCH/PYTHON compatibility
"""
# vim: sts=2 sw=2 ts=2


# Features
ENABLED_OPEN_LOGS=False
ENABLED_TICKET_NUMBERS=False
ENABLED_UPLOAD_DATA=False

# Main Kit
ARCHIVE_PASSWORD='Abracadabra'
KIT_NAME_FULL='WizardKit'
KIT_NAME_SHORT='WK'
SUPPORT_MESSAGE='Please let 2Shirt know by opening an issue on GitHub'

# Text Formatting
INDENT=4
WIDTH=32

# Live Linux
ROOT_PASSWORD='Abracadabra'
TECH_PASSWORD='Abracadabra'

# Time Zones
## See 'timedatectl list-timezones' for valid Linux values
## See 'tzutil /l' for valid Windows values
LINUX_TIME_ZONE='America/Denver'
WINDOWS_TIME_ZONE='Mountain Standard Time'


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
