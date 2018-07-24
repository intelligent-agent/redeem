"""
GCode M400
Wait until all buffered paths are executed

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from gcodes.GCodeCommand import GCodeCommand
import logging
import threading


class SyncState:
  def __init__(self):
    self.ready_event = threading.Event()
    self.used_event = False


class BufferedWaitEvent(GCodeCommand):
  def __init__(self, printer, event):
    super(BufferedWaitEvent, self).__init__(printer)
    self.event = event

  def execute(self, g):
    logging.debug("SyncBufferedToAsync_Buffered starting")
    self.event.wait()
    logging.debug("SyncBufferedToAsync_Buffered complete")

  def get_description(self):
    return "Internal"


class BufferedSyncEvent(GCodeCommand):
  def __init__(self, printer, path_planner_wait_event):
    super(BufferedSyncEvent, self).__init__(printer)
    self.path_planner_wait_event = path_planner_wait_event

  def execute(self, g):
    logging.debug("SyncAsyncToBuffered_Buffered firing event")
    self.path_planner_wait_event.signalWaitComplete()

  def get_description(self):
    return "Internal"
