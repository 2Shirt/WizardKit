"""WizardKit: Executable functions"""
#vim: sts=2 sw=2 ts=2

import re
import subprocess

import psutil


# Functions
def build_cmd_kwargs(cmd, minimized=False, pipe=True, shell=False, **kwargs):
  """Build kwargs for use by subprocess functions, returns dict.

  Specifically subprocess.run() and subprocess.Popen().
  NOTE: If no encoding specified then UTF-8 will be used.
  """
  cmd_kwargs = {
    'args': cmd,
    'shell': shell,
    }

  # Add additional kwargs if applicable
  for key in ('check', 'cwd', 'encoding', 'errors', 'stderr', 'stdout'):
    if key in kwargs:
      cmd_kwargs[key] = kwargs[key]

  # Default to UTF-8 encoding
  if not ('encoding' in cmd_kwargs or 'errors' in cmd_kwargs):
    cmd_kwargs['encoding'] = 'utf-8'
    cmd_kwargs['errors'] = 'ignore'

  # Start minimized
  if minimized:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 6
    cmd_kwargs['startupinfo'] = startupinfo


  # Pipe output
  if pipe:
    cmd_kwargs['stderr'] = subprocess.PIPE
    cmd_kwargs['stdout'] = subprocess.PIPE

  # Done
  return cmd_kwargs


def get_procs(name, exact=True):
  """Get process object(s) based on name, returns list of proc objects."""
  processes = []
  regex = f'^{name}$' if exact else name

  # Iterate over all processes
  for proc in psutil.process_iter():
    if re.search(regex, proc.name(), re.IGNORECASE):
      processes.append(proc)

  # Done
  return processes


def kill_procs(name, exact=True, force=False, timeout=30):
  """Kill all processes matching name (case-insensitively).

  NOTE: Under Posix systems this will send SIGINT to allow processes
        to gracefully exit.

  If force is True then it will wait until timeout specified and then
  send SIGKILL to any processes still alive.
  """
  target_procs = get_procs(name, exact=exact)
  for proc in target_procs:
    proc.terminate()

  # Force kill if necesary
  if force:
    results = psutil.wait_procs(target_procs, timeout=timeout)
    for proc in results[1]: # Alive processes
      proc.kill()


def popen_program(cmd, pipe=False, minimized=False, shell=False, **kwargs):
  """Run program and return a subprocess.Popen object."""
  cmd_kwargs = build_cmd_kwargs(
    cmd,
    minimized=minimized,
    pipe=pipe,
    shell=shell,
    **kwargs)

  # Ready to run program
  return subprocess.Popen(**cmd_kwargs)


def run_program(cmd, check=True, pipe=True, shell=False, **kwargs):
  """Run program and return a subprocess.CompletedProcess object."""
  cmd_kwargs = build_cmd_kwargs(
    cmd,
    check=check,
    pipe=pipe,
    shell=shell,
    **kwargs)

  # Ready to run program
  return subprocess.run(**cmd_kwargs)


def wait_for_procs(name, exact=True, timeout=None):
  """Wait for all process matching name."""
  target_procs = get_procs(name, exact=exact)
  results = psutil.wait_procs(target_procs, timeout=timeout)

  # Raise exception if necessary
  if results[1]: # Alive processes
    raise psutil.TimeoutExpired(name=name, seconds=timeout)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
