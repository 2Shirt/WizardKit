"""WizardKit: kit module init"""
# vim: sts=2 sw=2 ts=2

import platform

from . import tools

if platform.system() == 'Linux':
  from . import ufd
