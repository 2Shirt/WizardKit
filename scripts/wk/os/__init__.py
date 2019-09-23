"""WizardKit: os module init"""
# vim: sts=2 sw=2 ts=2

import platform

#if platform.system() == 'Darwin':
#if platform.system() == 'Linux':
if platform.system() == 'Windows':
  from wk.os import win
