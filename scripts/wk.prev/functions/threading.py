# Wizard Kit: Functions - Threading

from threading import Thread
from queue import Queue, Empty

# Classes
class NonBlockingStreamReader():
  """Class to allow non-blocking reads from a stream."""
  # Credits:
  ## https://gist.github.com/EyalAr/7915597
  ## https://stackoverflow.com/a/4896288

  def __init__(self, stream):
    self.stream = stream
    self.queue = Queue()

    def populate_queue(stream, queue):
      """Collect lines from stream and put them in queue."""
      while True:
        line = stream.read(1)
        if line:
          queue.put(line)

    self.thread = start_thread(
      populate_queue,
      args=(self.stream, self.queue))

  def read(self, timeout=None):
    try:
      return self.queue.get(block = timeout is not None,
          timeout = timeout)
    except Empty:
      return None


# Functions
def start_thread(function, args=[], daemon=True):
  """Run function as thread in background, returns Thread object."""
  thread = Thread(target=function, args=args, daemon=daemon)
  thread.start()
  return thread


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
