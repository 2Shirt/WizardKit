"""WizardKit: Execution functions"""
#vim: sts=2 sw=2 ts=2

import json
import logging
import os
import re
import subprocess
import time

from threading import Thread
from queue import Queue, Empty

import psutil


# STATIC VARIABLES
LOG = logging.getLogger(__name__)


# Classes
class NonBlockingStreamReader():
  """Class to allow non-blocking reads from a stream."""
  # pylint: disable=too-few-public-methods
  # Credits:
  ## https://gist.github.com/EyalAr/7915597
  ## https://stackoverflow.com/a/4896288

  def __init__(self, stream):
    self.stream = stream
    self.queue = Queue()

    def populate_queue(stream, queue):
      """Collect lines from stream and put them in queue."""
      while not stream.closed:
        try:
          line = stream.read(1)
        except ValueError:
          # Assuming the stream was closed
          line = None
        if line:
          queue.put(line)

    self.thread = start_thread(
      populate_queue,
      args=(self.stream, self.queue),
      )

  def stop(self):
    """Stop reading from input stream."""
    self.stream.close()

  def read(self, timeout=None):
    """Read from queue if possible, returns item from queue."""
    try:
      return self.queue.get(block=timeout is not None, timeout=timeout)
    except Empty:
      return None

  def save_to_file(self, proc, out_path):
    """Continuously save output to file while proc is running."""
    LOG.debug('Saving process %s output to %s', proc, out_path)
    while proc.poll() is None:
      out = b''
      out_bytes = b''
      while out is not None:
        out = self.read(0.1)
        if out:
          out_bytes += out
      with open(out_path, 'a', encoding='utf-8') as _f:
        _f.write(out_bytes.decode('utf-8', errors='ignore'))

    # Close stream to prevent 100% CPU usage
    self.stream.close()


# Functions
def build_cmd_kwargs(cmd, minimized=False, pipe=True, shell=False, **kwargs):
  """Build kwargs for use by subprocess functions, returns dict.

  Specifically subprocess.run() and subprocess.Popen().
  NOTE: If no encoding specified then UTF-8 will be used.
  """
  LOG.debug(
    'cmd: %s, minimized: %s, pipe: %s, shell: %s, kwargs: %s',
    cmd, minimized, pipe, shell, kwargs,
    )
  cmd_kwargs = {
    'args': cmd,
    'shell': shell,
    }

  # Strip sudo if appropriate
  if cmd[0] == 'sudo':
    if os.name == 'posix' and os.geteuid() == 0: # pylint: disable=no-member
      cmd.pop(0)

  # Add additional kwargs if applicable
  for key in 'check cwd encoding errors stderr stdin stdout'.split():
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
  LOG.debug('cmd_kwargs: %s', cmd_kwargs)
  return cmd_kwargs


def get_json_from_command(cmd, check=True, encoding='utf-8', errors='ignore'):
  """Capture JSON content from cmd output, returns dict.

  If the data can't be decoded then either an exception is raised
  or an empty dict is returned depending on errors.
  """
  LOG.debug('Loading JSON data from cmd: %s', cmd)
  json_data = {}

  try:
    proc = run_program(cmd, check=check, encoding=encoding, errors=errors)
    json_data = json.loads(proc.stdout)
  except (subprocess.CalledProcessError, json.decoder.JSONDecodeError):
    if errors != 'ignore':
      raise

  return json_data


def get_procs(name, exact=True, try_again=True):
  """Get process object(s) based on name, returns list of proc objects."""
  LOG.debug('name: %s, exact: %s', name, exact)
  processes = []
  regex = f'^{name}$' if exact else name

  # Iterate over all processes
  for proc in psutil.process_iter():
    if re.search(regex, proc.name(), re.IGNORECASE):
      processes.append(proc)

  # Try again?
  if not processes and try_again:
    time.sleep(1)
    processes = get_procs(name, exact, try_again=False)

  # Done
  return processes


def kill_procs(name, exact=True, force=False, timeout=30):
  """Kill all processes matching name (case-insensitively).

  NOTE: Under Posix systems this will send SIGINT to allow processes
        to gracefully exit.

  If force is True then it will wait until timeout specified and then
  send SIGKILL to any processes still alive.
  """
  LOG.debug(
    'name: %s, exact: %s, force: %s, timeout: %s',
    name, exact, force, timeout,
    )
  target_procs = get_procs(name, exact=exact)
  for proc in target_procs:
    proc.terminate()

  # Force kill if necesary
  if force:
    results = psutil.wait_procs(target_procs, timeout=timeout)
    for proc in results[1]: # Alive processes
      proc.kill()


def popen_program(cmd, minimized=False, pipe=False, shell=False, **kwargs):
  """Run program and return a subprocess.Popen object."""
  LOG.debug(
    'cmd: %s, minimized: %s, pipe: %s, shell: %s',
    cmd, minimized, pipe, shell,
    )
  LOG.debug('kwargs: %s', kwargs)
  cmd_kwargs = build_cmd_kwargs(
    cmd,
    minimized=minimized,
    pipe=pipe,
    shell=shell,
    **kwargs)
  try:
    # pylint: disable=consider-using-with
    proc = subprocess.Popen(**cmd_kwargs)
  except FileNotFoundError:
    LOG.error('Command not found: %s', cmd)
    raise
  LOG.debug('proc: %s', proc)

  # Done
  return proc


def run_program(cmd, check=True, pipe=True, shell=False, **kwargs):
  # pylint: disable=subprocess-run-check
  """Run program and return a subprocess.CompletedProcess object."""
  LOG.debug(
    'cmd: %s, check: %s, pipe: %s, shell: %s',
    cmd, check, pipe, shell,
    )
  LOG.debug('kwargs: %s', kwargs)
  cmd_kwargs = build_cmd_kwargs(
    cmd,
    check=check,
    pipe=pipe,
    shell=shell,
    **kwargs)
  try:
    proc = subprocess.run(**cmd_kwargs)
  except FileNotFoundError:
    LOG.error('Command not found: %s', cmd)
    raise
  LOG.debug('proc: %s', proc)

  # Done
  return proc


def start_thread(function, args=None, daemon=True):
  """Run function as thread in background, returns Thread object."""
  LOG.debug(
    'Starting background thread for function: %s, args: %s, daemon: %s',
    function, args, daemon,
    )
  args = args if args else []
  thread = Thread(target=function, args=args, daemon=daemon)
  thread.start()
  return thread


def stop_process(proc, graceful=True):
  """Stop process.

  NOTES:  proc should be a subprocess.Popen obj.
          If graceful is True then a SIGTERM is sent before SIGKILL.
  """

  # Graceful exit
  if graceful:
    if os.name == 'posix' and os.geteuid() != 0: # pylint: disable=no-member
      run_program(['sudo', 'kill', str(proc.pid)], check=False)
    else:
      proc.terminate()
    time.sleep(2)

  # Force exit
  if os.name == 'posix' and os.geteuid() != 0: # pylint: disable=no-member
    run_program(['sudo', 'kill', '-9', str(proc.pid)], check=False)
  else:
    proc.kill()


def wait_for_procs(name, exact=True, timeout=None):
  """Wait for all process matching name."""
  LOG.debug('name: %s, exact: %s, timeout: %s', name, exact, timeout)
  target_procs = get_procs(name, exact=exact)
  procs = psutil.wait_procs(target_procs, timeout=timeout)

  # Raise exception if necessary
  if procs[1]: # Alive processes
    raise psutil.TimeoutExpired(name=name, seconds=timeout)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
