"""WizardKit: repairs module init"""
# vim: sts=2 sw=2 ts=2

import platform

if platform.system() == 'Windows':
  from wk.repairs import win
