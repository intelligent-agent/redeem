"""
GCode processor processing GCode commands with a plugin system


Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
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
from gcodes import GCodeCommand
import Sync
try:
    from Gcode import Gcode
except ImportError:
    from redeem.Gcode import Gcode


class GCodeProcessor:
    def __init__(self, printer):
        self.printer = printer

        self.sync_event_needed = False

        self.gcodes = {}
        try:
            module = __import__("gcodes", locals(), globals())
        except ImportError:
            module = importlib.import_module("redeem.gcodes")
        self.load_classes_in_module(module)

    def load_classes_in_module(self, module):
        for module_name, obj in inspect.getmembers(module):
            if inspect.ismodule(obj) and \
                    (obj.__name__.startswith('gcodes') or
                     obj.__name__.startswith('redeem.gcodes')):
                self.load_classes_in_module(obj)
            elif inspect.isclass(obj) and \
                    not inspect.isabstract(obj) and \
                    issubclass(obj, GCodeCommand.GCodeCommand) and \
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
            logging.warning(
                "tried to resolve a gcode that's already resolved: " + gcode.message)
            logging.error(traceback.format_stack())
        else:
            gcode.command = self.gcodes[gcode.code()]

    def is_buffered(self, gcode):
        return gcode.command.is_buffered()

    def is_sync(self, gcode):
        return gcode.command.is_sync()

    def is_async(self, gcode):
        return gcode.command.is_async()

    def synchronize(self, gcode):
        try:
            gcode.command.on_sync(gcode)
        except Exception as e:
            logging.error("Error while executing " +
                          gcode.code() + ": " + str(e))
        return gcode

    def execute(self, gcode):
        if not hasattr(gcode, 'command'):
            logging.warning(
                "tried to execute a gcode wasn't resolved: " + gcode.message)
            # logging.error(traceback.format_stack())
            self.resolve(gcode)

        try:
            gcode.command.execute(gcode)
        except Exception as e:
            logging.error("Error while executing " +
                          gcode.code() + ": " + str(e))
            logging.error(traceback.format_exc(sys.exc_info()[2]))
        return gcode

    def enqueue(self, gcode):
        self.resolve(gcode)

        # If an M116 is running, peek at the incoming Gcode
        if self.peek(gcode):
            return

        if self.is_async(gcode):
            self.sync_event_needed = True
            self.printer.async_commands.put(gcode)

        elif self.is_buffered(gcode):
            # if we previously queued an async code, we need to queue an event to get back into sync
            if self.sync_event_needed:
                logging.info("adding sync before " + gcode.message)
                self._make_buffered_queue_wait_for_async_queue()
                self.sync_event_needed = False

            self.printer.commands.put(gcode)

            if self.is_sync(gcode):
                # Yes, it goes into both queues!
                self.printer.sync_commands.put(gcode)
        else:
            self.printer.unbuffered_commands.put(gcode)

        if gcode.code() in ["M109", "M190"]:
            self._make_async_queue_wait_for_buffered_queue()

    def peek(self, gcode):
        if self.printer.running_M116 and gcode.code() == "M108":
            self.execute(gcode)
            return True
        return False

    def get_long_description(self, gcode):
        val = gcode.code()[:-1]
        if not val in self.gcodes:
            logging.error(
                "No GCode processor for " + gcode.code() +
                ". Message: " + gcode.message)
            return "GCode " + gcode.code() + " is not implemented"
        try:
            return self.gcodes[val].get_long_description()
        except Exception as e:
            logging.error(
                "Error while getting long description on " + gcode.code() + ": " + str(e))
        return "Error getting long decription for " + str(val)

    def get_test_gcodes(self):
        gcodes = []
        for name, gcode in iteritems(self.gcodes):
            for str in gcode.get_test_gcodes():
                gcodes.append(Gcode({"message": str, "prot": "Test"}))
        return gcodes

    def _make_buffered_queue_wait_for_async_queue(self):
        logging.info("queueing buffered-to-async sync event")
        state = Sync.SyncState()
        buffered = Sync.SyncBufferedToAsync_Buffered(self.printer, state)
        async = Sync.SyncBufferedToAsync_Async(self.printer, state)

        buffered_gcode = Gcode(
            {"message": "SyncBufferedToAsync_Buffered", "prot": "internal"})
        buffered_gcode.command = buffered

        async_gcode = Gcode(
            {"message": "SyncBufferedToAsync_Async", "prot": "internal"})
        async_gcode.command = async

        self.printer.commands.put(buffered_gcode)
        self.printer.sync_commands.put(async_gcode)
        self.printer.async_commands.put(async_gcode)
        logging.info("done queueing buffered-to-async sync event")

    def _make_async_queue_wait_for_buffered_queue(self):
        logging.info("queueing async-to-buffered sync event")
        state = Sync.SyncState()
        buffered = Sync.SyncAsyncToBuffered_Buffered(self.printer, state)
        async = Sync.SyncAsyncToBuffered_Async(self.printer, state)

        buffered_gcode = Gcode(
            {"message": "SyncAsyncToBuffered_Buffered", "prot": "internal"})
        buffered_gcode.command = buffered

        async_gcode = Gcode(
            {"message": "SyncAsyncToBuffered_Async", "prot": "internal"})
        async_gcode.command = async

        self.printer.async_commands.put(async_gcode)
        self.printer.commands.put(buffered_gcode)
        logging.info("done queueing async-to-buffered sync event")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    proc = GCodeProcessor({})

    print("")
    print("Commands:")

    descriptions = proc.get_supported_commands_and_description()

    def _natural_key(string_):
        """See http://www.codinghorror.com/blog/archives/001018.html"""
        return [int(s) if s.isdigit() else
                s for s in re.split(r'(\d+)', string_)]

    for name in sorted(descriptions, key=_natural_key):
        print(name + "\t" + descriptions[name])
