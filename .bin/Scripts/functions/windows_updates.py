# Wizard Kit: Functions - Windows updates

from functions.common import *


# Functions
def delete_folder(folder_path):
  """Near-useless wrapper for shutil.rmtree."""
  shutil.rmtree(folder_path)


def disable_service(service_name):
  """Set service startup to disabled."""
  run_program(['sc', 'config', service_name, 'start=', 'disabled'])

  # Verify service was disabled
  start_type = get_service_start_type(service_name)
  if not start_type.lower().startswith('disabled'):
    raise GenericError('Failed to disable service {}'.format(service_name))


def disable_windows_updates():
  """Disable windows updates and clear SoftwareDistribution folder."""
  indent=2
  width=52
  update_folders = [
    r'{WINDIR}\SoftwareDistribution'.format(**global_vars['Env']),
    r'{SYSTEMDRIVE}\$WINDOWS.~BT'.format(**global_vars['Env']),
  ]

  for service in ('wuauserv', 'bits'):
    # Stop service
    result = try_and_print(
      'Stopping service {}...'.format(service),
      indent=indent, width=width,
      function=stop_service, service_name=service)
    if not result['CS']:
      result = try_and_print(
        'Stopping service {}...'.format(service),
        indent=indent, width=width,
        function=stop_service, service_name=service)
      if not result['CS']:
        raise GenericError('Service {} could not be stopped.'.format(service))

    # Disable service
    result = try_and_print(
      'Disabling service {}...'.format(service),
      indent=indent, width=width,
      function=disable_service, service_name=service)
    if not result['CS']:
      result = try_and_print(
        'Disabling service {}...'.format(service),
        indent=indent, width=width,
        function=disable_service, service_name=service)
      if not result['CS']:
        raise GenericError('Service {} could not be disabled.'.format(service))

  # Delete update folders
  for folder_path in update_folders:
    if os.path.exists(folder_path):
      result = try_and_print(
        'Deleting folder {}...'.format(folder_path),
        indent=indent, width=width,
        function=delete_folder, folder_path=folder_path)
      if not result['CS']:
        raise GenericError('Failed to remove folder {}'.format(folder_path))


def enable_service(service_name, start_type='auto'):
  """Enable service by setting start type."""
  run_program(['sc', 'config', service_name, 'start=', start_type])


def enable_windows_updates(silent=False):
  """Enable windows updates"""
  indent=2
  width=52

  for service in ('bits', 'wuauserv'):
    # Enable service
    start_type = 'auto'
    if service == 'wuauserv':
      start_type = 'demand'
    if silent:
      try:
        enable_service(service, start_type=start_type)
      except Exception:
        # Try again
        enable_service(service, start_type=start_type)
    else:
      result = try_and_print(
        'Enabling service {}...'.format(service),
        indent=indent, width=width,
        function=enable_service, service_name=service, start_type=start_type)
      if not result['CS']:
        result = try_and_print(
          'Enabling service {}...'.format(service),
          indent=indent, width=width,
          function=enable_service, service_name=service, start_type=start_type)
        if not result['CS']:
          raise GenericError('Service {} could not be enabled.'.format(service))


def get_service_status(service_name):
  """Get service status using psutil, returns str."""
  status = 'Unknown'
  try:
    service = psutil.win_service_get(service_name)
    status = service.status()
  except psutil.NoSuchProcess:
    # Ignore and return 'Unknown' below
    pass

  return status


def get_service_start_type(service_name):
  """Get service startup type using psutil, returns str."""
  start_type = 'Unknown'
  try:
    service = psutil.win_service_get(service_name)
    start_type = service.start_type()
  except psutil.NoSuchProcess:
    # Ignore and return 'Unknown' below
    pass

  return start_type


def stop_service(service_name):
  """Stop service."""
  run_program(['net', 'stop', service_name], check=False)

  # Verify service was stopped
  status = get_service_status(service_name)
  if not status.lower().startswith('stopped'):
    raise GenericError('Failed to stop service {}'.format(service_name))


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
