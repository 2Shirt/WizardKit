"""WizardKit: Log Functions"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
import shutil
import time

from wk import cfg
from wk.io import non_clobber_path


# STATIC VARIABLES
if os.path.exists('/.wk-live-macos'):
  # Workaround for live macOS env
  DEFAULT_LOG_DIR = '/var/log/WizardKit'
elif os.name == 'nt':
  # Example: "C:\WK\1955-11-05\WizardKit"
  DEFAULT_LOG_DIR = (
    f'{os.environ.get("SYSTEMDRIVE", "C:")}/'
    f'{cfg.main.KIT_NAME_SHORT}/'
    f'{time.strftime("%Y-%m-%d")}'
    )
else:
  # Example: "/home/tech/Logs"
  DEFAULT_LOG_DIR = f'{os.path.expanduser("~")}/Logs'
DEFAULT_LOG_NAME = cfg.main.KIT_NAME_FULL


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


def format_log_path(
    log_dir=None, log_name=None, timestamp=False,
    kit=False, tool=False):
  """Format path based on args passed, returns pathlib.Path obj."""
  log_path = pathlib.Path(
    f'{log_dir if log_dir else DEFAULT_LOG_DIR}/'
    f'{cfg.main.KIT_NAME_FULL+"/" if kit else ""}'
    f'{"Tools/" if tool else ""}'
    f'{log_name if log_name else DEFAULT_LOG_NAME}'
    f'{"_" if timestamp else ""}'
    f'{time.strftime("%Y-%m-%d_%H%M%S%z") if timestamp else ""}'
    '.log'
    )
  log_path = log_path.resolve()

  # Avoid clobbering
  log_path = non_clobber_path(log_path)

  # Done
  return log_path


def get_root_logger_path():
  """Get path to log file from root logger, returns pathlib.Path obj."""
  log_path = None
  root_logger = logging.getLogger()

  # Check all handlers and use the first fileHandler found
  for handler in root_logger.handlers:
    if isinstance(handler, logging.FileHandler):
      log_path = pathlib.Path(handler.baseFilename).resolve()
      break

  # Done
  return log_path


def remove_empty_log():
  """Remove log if empty."""
  is_empty = False

  # Check if log is empty
  log_path = get_root_logger_path()
  try:
    is_empty = log_path and log_path.exists() and log_path.stat().st_size == 0
  except (FileNotFoundError, AttributeError):
    # File doesn't exist or couldn't verify it's empty
    pass

  # Delete log
  if is_empty:
    log_path.unlink()


def start(config=None):
  """Configure and start logging using safe defaults."""
  log_path = format_log_path(timestamp=os.name != 'nt')
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
  atexit.register(remove_empty_log)
  atexit.register(logging.shutdown)


def update_log_path(
    dest_dir=None, dest_name=None, keep_history=True, timestamp=True):
  """Moves current log file to new path and updates the root logger."""
  root_logger = logging.getLogger()
  cur_handler = None
  cur_path = get_root_logger_path()
  new_path = format_log_path(dest_dir, dest_name, timestamp=timestamp)
  os.makedirs(new_path.parent, exist_ok=True)

  # Get current logging file handler
  for handler in root_logger.handlers:
    if isinstance(handler, logging.FileHandler):
      cur_handler = handler
      break
  if not cur_handler:
    raise RuntimeError('Logging FileHandler not found')

  # Copy original log to new location
  if keep_history:
    if new_path.exists():
      raise FileExistsError(f'Refusing to clobber: {new_path}')
    shutil.move(cur_path, new_path)

  # Remove old log if empty
  remove_empty_log()

  # Create new cur_handler (preserving formatter settings)
  new_handler = logging.FileHandler(new_path, mode='a')
  new_handler.setFormatter(cur_handler.formatter)

  # Replace current handler
  root_logger.removeHandler(cur_handler)
  root_logger.addHandler(new_handler)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
