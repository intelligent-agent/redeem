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


class SyncBufferedToAsync_Buffered(GCodeCommand):
    def __init__(self, printer, sync_state):
        super(SyncBufferedToAsync_Buffered, self).__init__(printer)
        self.sync_state = sync_state

    def execute(self, g):
        logging.debug("SyncBufferedToAsync_Buffered starting")
        self.sync_state.ready_event.wait()
        logging.debug("SyncBufferedToAsync_Buffered got ready event")
        if not self.sync_state.used_event:
            logging.debug("SyncBufferedToAsync_Buffered has to wait manually")
            # The move buffer is already empty! fallback to this to ensure we're in sync.
            self.printer.path_planner.wait_until_done()
        logging.debug("SyncBufferedToAsync_Buffered complete")

    def get_description(self):
        return "Internal"


class SyncBufferedToAsync_Async(GCodeCommand):
    def __init__(self, printer, sync_state):
        super(SyncBufferedToAsync_Async, self).__init__(printer)
        self.sync_state = sync_state

    def execute(self, g):
        logging.debug("SyncBufferedToAsync_Async starting")
        # This needs to be a standard method somewhere
        # No blocking of the PRU, (notification only)
        if not self.printer.path_planner.queue_sync_event(False):
            logging.debug(
                "SyncBufferedToAsync_Async failed to queue a sync event - waiting until done instead")
            self.sync_state.used_event = False
            self.sync_state.ready_event.set()
            self.printer.sync_commands.get()
            # We should be at the front of the line.
            self.printer.sync_commands.task_done()
        logging.debug("SyncBufferedToAsync_Async complete")

    def on_sync(self, g):
        logging.debug("SyncBufferedToAsync_Async on_sync")
        self.sync_state.used_event = True
        self.sync_state.ready_event.set()

    def get_description(self):
        return "Internal"


class SyncAsyncToBuffered_Buffered(GCodeCommand):
    def __init__(self, printer, sync_state):
        super(SyncAsyncToBuffered_Buffered, self).__init__(printer)
        self.sync_state = sync_state

    def execute(self, g):
        logging.debug("SyncAsyncToBuffered_Buffered firing event")
        self.sync_state.used_event = False
        self.sync_state.ready_event.set()

    def get_description(self):
        return "Internal"


class SyncAsyncToBuffered_Async(GCodeCommand):
    def __init__(self, printer, sync_state):
        super(SyncAsyncToBuffered_Async, self).__init__(printer)
        self.sync_state = sync_state

    def execute(self, g):
        logging.debug("SyncAsyncToBuffered_Async waiting for event")
        self.sync_state.ready_event.wait()
        logging.debug("SyncAsyncToBuffered_Async event has fired - continuing")

    def get_description(self):
        return "Internal"
