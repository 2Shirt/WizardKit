"""WizardKit: os module init"""
# vim: sts=2 sw=2 ts=2

import os

if os.name == 'nt':
  from wk.os import win
