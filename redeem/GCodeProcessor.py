"""
GCode processor processing GCode commands with a plugin system


Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import traceback
import inspect
import logging
import re
import importlib
from threading import Event
from six import iteritems
from gcodes.GCodeCommand import GCodeCommand
from PathPlanner import SyncCallback
import Sync
try:
  from Gcode import Gcode
except ImportError:
  from redeem.Gcode import Gcode


class GCodePerformanceCounters:
  def __init__(self):
    self.gcodes_executed = 0
    self.start_time = 0


class GCodeProcessor:
  def __init__(self, printer):
    self.printer = printer
    self.counters = GCodePerformanceCounters()
    self.sync_event_needed = False
    self.gcodes = {}
    module = importlib.import_module("redeem.gcodes")
    self.load_classes_in_module(module)

    if len(self.gcodes) is 0:
      logging.error("No gcodes loaded")

  def load_classes_in_module(self, module):
    for module_name, obj in inspect.getmembers(module):
      if inspect.ismodule(obj) and \
              (obj.__name__.startswith('gcodes') or
               obj.__name__.startswith('redeem.gcodes')):
        self.load_classes_in_module(obj)
      elif inspect.isclass(obj) and \
              not inspect.isabstract(obj) and \
              issubclass(obj, GCodeCommand) and \
              module_name != 'GCodeCommand' and \
              module_name != 'ToolChange':
        logging.debug("Loading GCode handler " + module_name + "...")
        self.gcodes[module_name] = obj(self.printer)

  def override_command(self, gcode, gcodeClassInstance):
    """
    This methods allow a plugin to replace a GCode command
    with its own provided class.
    """
    self.gcodes[gcode] = gcodeClassInstance

  def get_supported_commands(self):
    ret = []
    for gcode in self.gcodes:
      ret.append(gcode)
    return ret

  def get_supported_commands_and_description(self):
    ret = {}
    for gcode in self.gcodes:
      ret[gcode] = self.gcodes[gcode].get_description()
    return ret

  def resolve(self, gcode):
    if hasattr(gcode, 'command'):
      logging.warning("tried to resolve a gcode that's already resolved: " + gcode.message)
      logging.error(traceback.format_stack())
    else:
      c = gcode.code() if not gcode.is_info_command() else gcode.code()[:-1]
      if not c in self.gcodes:
        if c != "No-Gcode":
          logging.error("No GCode processor for " + gcode.code() + ". Message: " + gcode.message)
        gcode.command = None
      else:
        gcode.command = self.gcodes[c]

  def synchronize(self, gcode):
    try:
      gcode.command.on_sync(gcode)
    except Exception as e:
      logging.error("Error while executing " + gcode.code() + ": " + str(e))
    return gcode

  def execute(self, gcode):
    if not hasattr(gcode, 'command'):
      logging.warning("tried to execute a gcode that wasn't resolved: " + gcode.message)
      # logging.error(traceback.format_stack())
      self.resolve(gcode)
    if gcode.command is None:
      return

    self.counters.gcodes_executed += 1

    try:
      gcode.command.execute(gcode)
    except Exception as e:
      logging.error("Error while executing " + gcode.code() + ": " + str(e))
      logging.error(traceback.format_exc(sys.exc_info()[2]))
    return gcode

  def enqueue(self, gcode):
    self.resolve(gcode)
    if gcode.command is None:
      logging.warning("tried to enqueue an unknown gcode: " + gcode.code())
      gcode.set_answer("ok Unknown GCode: " + gcode.code())
      self.printer.reply(gcode)
      return

    # If an M116 is running, peek at the incoming Gcode
    if self.peek(gcode):
      return
    if gcode.command.is_async():
      self.sync_event_needed = True
      self.execute(gcode)
      self.printer.reply(gcode)
    elif gcode.command.is_buffered():
      # if we previously queued an async code, we need to queue an event to get back into sync
      if self.sync_event_needed:
        logging.info("adding sync before " + gcode.message)
        self._make_buffered_queue_wait_for_async_queue()
        self.sync_event_needed = False
      self.printer.commands.put(gcode)
    else:
      self.printer.unbuffered_commands.put(gcode)
    if gcode.code() in ["M109", "M190"]:
      self._make_async_queue_wait_for_buffered_queue()

  def peek(self, gcode):
    if self.printer.running_M116 and gcode.code() in ["M108", "M104", "M140"]:
      self.execute(gcode)
      return True
    elif gcode.code() == "M1500":
      gcode.command.execute_custom(gcode, self.counters)
    return False

  def get_long_description(self, gcode):
    val = gcode.code()[:-1]
    if not val in self.gcodes:
      logging.error("No GCode processor for " + gcode.code() + ". Message: " + gcode.message)
      return "GCode " + gcode.code() + " is not implemented"
    try:
      return self.gcodes[val].get_long_description()
    except Exception as e:
      logging.error("Error while getting long description on " + gcode.code() + ": " + str(e))
    return "Error getting long decription for " + str(val)

  def get_test_gcodes(self):
    gcodes = []
    for name, gcode in iteritems(self.gcodes):
      for str in gcode.get_test_gcodes():
        gcodes.append(Gcode({"message": str, "prot": "Test"}))
    return gcodes

  def _make_buffered_queue_wait_for_async_queue(self):
    logging.info("queueing buffered-to-async sync event")
    event = Event()
    callback = SyncCallback(event)

    self.printer.path_planner.native_planner.queueSyncEvent(callback, False)

    buffered = Sync.BufferedWaitEvent(self.printer, event)
    buffered_gcode = Gcode({"message": "SyncBufferedToAsync_Buffered", "prot": "internal"})
    buffered_gcode.command = buffered

    # buffered doesn't actually use this, but we need it to stay alive per the garbage collector
    buffered.native_callback = callback

    self.printer.commands.put(buffered_gcode)
    logging.info("done queueing buffered-to-async sync event")

  def _make_async_queue_wait_for_buffered_queue(self):
    logging.info("queueing async-to-buffered sync event")

    wait_event = self.printer.path_planner.native_planner.queueWaitEvent()

    buffered = Sync.BufferedSyncEvent(self.printer, wait_event)
    buffered_gcode = Gcode({"message": "SyncAsyncToBuffered_Buffered", "prot": "internal"})
    buffered_gcode.command = buffered

    self.printer.commands.put(buffered_gcode)
    logging.info("done queueing async-to-buffered sync event")


if __name__ == '__main__':
  logging.basicConfig(
      level=logging.DEBUG,
      format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
      datefmt='%m-%d %H:%M')

  proc = GCodeProcessor({})

  print("")
  print("Commands:")

  descriptions = proc.get_supported_commands_and_description()

  def _natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

  for name in sorted(descriptions, key=_natural_key):
    print(name + "\t" + descriptions[name])
