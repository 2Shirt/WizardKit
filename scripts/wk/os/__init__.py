"""WizardKit: os module init"""
# vim: sts=2 sw=2 ts=2

import platform

if platform.system() == 'Darwin':
  from . import mac
if platform.system() == 'Linux':
  from . import linux
if platform.system() == 'Windows':
  from . import win
