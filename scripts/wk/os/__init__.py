"""WizardKit: os module init"""
# vim: sts=2 sw=2 ts=2

import platform

#if platform.system() == 'Darwin':
if platform.system() == 'Linux':
  from wk.os import linux
if platform.system() == 'Windows':
  from wk.os import win
