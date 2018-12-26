import threading
import os
import select
import sys
import Queue
import logging


class IOManager:
  thread = None
  control_pipe = None
  control_queue = None

  def __init__(self):
    self.control_queue = Queue.Queue()
    read_fd, write_fd = os.pipe()
    self.control_pipe = os.fdopen(write_fd, 'w')
    thread_pipe = os.fdopen(read_fd, 'r')
    logging.debug("IOManager starting up")
    self.thread = threading.Thread(target=self._thread_loop, name="IOManager", args=[thread_pipe])
    self.thread.start()

  def stop(self):
    logging.debug("IOManager shutting down")

    def stop_handler(poller, callbacks):
      return False

    self.control_queue.put(stop_handler)
    self._wake_io_thread()
    self.control_queue.join()
    self.thread.join()
    logging.debug("IOManager finished shutting down")

  def is_running(self):
    return self.thread is not None and self.thread.is_alive()

  def add_file(self, file, callback):
    logging.debug("IOManager adding file: %s", str(file))

    def add_handler(poller, callbacks):
      poller.register(
          file, select.POLLIN | select.POLLPRI | select.POLLERR | select.POLLHUP | select.POLLNVAL)
      callbacks[file.fileno()] = callback
      logging.debug("IOManager thread added file successfully")
      return True

    self.control_queue.put(add_handler)
    self._wake_io_thread()
    self.control_queue.join()

  def remove_file(self, file):
    logging.debug("IOManager removing file: %s", str(file))

    def remove_handler(poller, callbacks):
      poller.unregister(file)
      del callbacks[file.fileno()]
      logging.debug("IOManager thread removed file successfully")
      return True

    self.control_queue.put(remove_handler)
    self._wake_io_thread()
    self.control_queue.join()

  def _wake_io_thread(self):
    self.control_pipe.write(" ")
    self.control_pipe.flush()

  def _thread_loop(self, control_pipe):
    try:
      keep_running = True
      callbacks = {}
      poller = select.poll()
      poller.register(control_pipe)
      while keep_running:
        active_fds = poller.poll()
        for fd, flag in active_fds:
          if fd == control_pipe.fileno():
            logging.debug("IOManagerThread processing control events")
            keep_running = self._handle_events(control_pipe, poller, callbacks)
            logging.debug("IOManagerThread finished processing control events")
          else:
            try:
              logging.debug("IOManagerThread calling callback %s with flags %s", str(fd), str(flag))
              callbacks[fd](flag)
            except:
              logging.warn("IOManager caught exception from a callback: %s", str(sys.exc_info()))
    except:
      logging.error("IOManager terminating due to %s", str(sys.exc_info()))
    logging.debug("IOManager terminating")

  def _handle_events(self, control_pipe, poller, callbacks):
    control_pipe.read(1)
    keep_running = True
    while not self.control_queue.empty():
      control_item = self.control_queue.get_nowait()
      keep_running = keep_running and control_item(poller, callbacks)
      self.control_queue.task_done()
      logging.debug("IOManager finished control item")
    return keep_running
