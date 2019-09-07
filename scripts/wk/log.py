'''WizardKit: Log Functions'''
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
import shutil
import time

from wk import cfg


# Functions
def enable_debug_mode():
  """Configures logging for better debugging."""
  root_logger = logging.getLogger()
  for handler in root_logger.handlers:
    formatter = logging.Formatter(
      datefmt=cfg.log.DEBUG['datefmt'],
      fmt=cfg.log.DEBUG['format'],
      )
    handler.setFormatter(formatter)
  root_logger.setLevel('DEBUG')


def start(config=None):
  """Configure and start logging using safe defaults."""
  if os.name == 'nt':
    log_path = '{drive}/{short}/Logs/{date}/{full}/{datetime}.log'.format(
      drive=os.environ.get('SYSTEMDRIVE', 'C:'),
      short=cfg.main.KIT_NAME_SHORT,
      date=time.strftime('%Y-%m-%d'),
      full=cfg.main.KIT_NAME_FULL,
      datetime=time.strftime('%Y-%m-%d_%H%M%S%z'),
      )
  else:
    log_path = '{home}/Logs/{full}_{datetime}.log'.format(
      home=os.path.expanduser('~'),
      full=cfg.main.KIT_NAME_FULL,
      datetime=time.strftime('%Y-%m-%d_%H%M%S%z'),
      )
  log_path = pathlib.Path(log_path).resolve()
  root_logger = logging.getLogger()

  # Safety checks
  if not config:
    config = cfg.log.DEFAULT
  if root_logger.hasHandlers():
    raise UserWarning('Logging already started, results may be unpredictable.')

  # Create log_dir
  os.makedirs(log_path.parent, exist_ok=True)

  # Config logger
  logging.basicConfig(filename=log_path, **config)

  # Register shutdown to run atexit
  atexit.register(logging.shutdown)


def update_log_path(dest_dir, dest_name=''):
  """Copies current log file to new dir and updates the root logger.

  NOTE: A timestamp and extension will be added to dest_name if provided.
  """
  root_logger = logging.getLogger()
  cur_handler = root_logger.handlers[0]
  dest = pathlib.Path(dest_dir)
  dest = dest.expanduser()
  if dest_name:
    dest_name = f'{dest_name}_{time.strftime("%Y-%m-%d_%H%M%S%z")}.log'

  # Safety checks
  if len(root_logger.handlers) > 1:
    raise RuntimeError('Multiple handlers not supported')
  if not isinstance(cur_handler, logging.FileHandler):
    raise RuntimeError('Only FileHandlers are supported')

  # Copy original log to new location
  source = pathlib.Path(cur_handler.baseFilename)
  source = source.resolve()
  if dest_name:
    dest = dest.joinpath(dest_name)
  else:
    dest = dest.joinpath(source.name)
  dest = dest.resolve()
  if dest.exists():
    raise FileExistsError(f'Refusing to clobber: {dest}')
  os.makedirs(dest.parent, exist_ok=True)
  shutil.copy(source, dest)

  # Create new cur_handler (preserving formatter settings)
  new_handler = logging.FileHandler(dest, mode='a')
  new_handler.setFormatter(cur_handler.formatter)

  # Replace current handler
  root_logger.removeHandler(cur_handler)
  root_logger.addHandler(new_handler)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
