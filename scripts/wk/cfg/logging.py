'''WizardKit: Config - Logging'''
# vim: sts=2 sw=2 ts=2

import logging


DEBUG = {
  'level': logging.DEBUG,
  'format': '[%(asctime)s %(levelname)s] [%(name)s.%(funcName)s] %(message)s',
  'datefmt': '%Y-%m-%d %H:%M:%S %z',
  }
DEFAULT = {
  'level': logging.INFO,
  'format': '[%(asctime)s %(levelname)s] %(message)s',
  'datefmt': '%Y-%m-%d %H:%M:%S %z',
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
