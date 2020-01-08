"""WizardKit: kit module init"""
# vim: sts=2 sw=2 ts=2

import platform

if platform.system() == 'Linux':
  from wk.kit import ufd
