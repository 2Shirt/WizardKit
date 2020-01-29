"""WizardKit: macOS Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import re

from wk.exe import run_program


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
REGEX_FANS = re.compile(r'^.*\(bytes (?P<bytes>.*)\)$')


# Functions
def decode_smc_bytes(text):
  """Decode SMC bytes, returns int."""
  result = None

  # Get bytes
  match = REGEX_FANS.match(text)
  if not match:
    LOG.error('Failed to decode smc output: %s', text)
    raise ValueError(f'Failed to decocde smc output: {text}')

  # Convert to text
  result = match.group('bytes')
  result = result.replace(' ', '')
  result = int(result, 16)

  # Done
  return result


def set_fans(mode):
  """Set fans to auto or max."""
  if mode == 'auto':
    set_fans_auto()
  elif mode == 'max':
    set_fans_max()
  else:
    raise RuntimeError(f'Invalid fan mode: {mode}')


def set_fans_auto():
  """Set fans to auto."""
  LOG.info('Setting fans to auto')
  cmd = ['sudo', 'smc', '-k', 'FS! ', '-w', '0000']
  run_program(cmd)


def set_fans_max():
  """Set fans to their max speeds."""
  LOG.info('Setting fans to max')
  num_fans = 0

  # Get number of fans
  cmd = ['smc', '-k', 'FNum', '-r']
  proc = run_program(cmd)
  num_fans = decode_smc_bytes(proc.stdout)
  LOG.info('Found %s fans', num_fans)

  # Set all fans to forced speed
  ## NOTE: mask is bit mask from right to left enabling fans
  ##       e.g. bit 1 is fan 0, bit 2 is fan 1, etc
  ##       So the mask for two fans is 0b11 or 0x3, four would be 0b111 or 0x7
  mask = f'{hex(2**num_fans - 1)[2:]:0>4}'
  cmd = ['sudo', 'smc', '-k', 'FS! ', '-w', mask]
  run_program(cmd)

  # Set all fans to their max speed
  for fan in range(num_fans):
    cmd = ['smc', '-k', f'F{fan}Mx', '-r']
    proc = run_program(cmd)
    max_temp = decode_smc_bytes(proc.stdout)
    LOG.info('Setting fan #%s to %s RPM', fan, str(max_temp >> 2))
    cmd = ['sudo', 'smc', '-k', f'F{fan}Tg', '-w', hex(max_temp)[2:]]
    run_program(cmd)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
