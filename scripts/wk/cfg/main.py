'''WizardKit: Config - Main

NOTE: A non-standard format is used for BASH/BATCH/PYTHON compatibility'''
# pylint: disable=bad-whitespace
# vim: sts=2 sw=2 ts=2


# Features
ENABLED_OPEN_LOGS = False
ENABLED_TICKET_NUMBERS = False
ENABLED_UPLOAD_DATA = False

# Main Kit
ARCHIVE_PASSWORD='Abracadabra'
KIT_NAME_FULL='WizardKit'
KIT_NAME_SHORT='WK'
SUPPORT_MESSAGE='Please let 2Shirt know by opening an issue on GitHub'

# Live Linux
ROOT_PASSWORD='Abracadabra'
TECH_PASSWORD='Abracadabra'

# Time Zones
LINUX_TIME_ZONE='America/Denver'            # See 'timedatectl list-timezones' for valid values
WINDOWS_TIME_ZONE='Mountain Standard Time'  # See 'tzutil /l' for valid values


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
