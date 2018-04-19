"""
GCode M400
Wait until all buffered paths are executed

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
import logging
import threading


class M400(GCodeCommand):

    def execute(self, g):
        logging.info("M400 starting")
        # This needs to be a standard method somewhere
        # No blocking of the PRU, (notification only)
        if not self.printer.path_planner.queue_sync_event(False):
            logging.info(
                "M400 failed to queue a sync event - waiting until done instead")
            # The move buffer is already empty! fallback to this to ensure we're in sync.
            self.printer.path_planner.wait_until_done()
            self.printer.sync_commands.get()
            # We should be at the front of the line.
            self.printer.sync_commands.task_done()
        logging.info("M400 complete")

    def on_sync(self, g):
        logging.info("M400 on_sync")
        # self.printer.path_planner.clear_sync_event()  # Only needed if blocking the PRU

    def get_description(self):
        return "Wait until all buffered paths are executed"

    def is_buffered(self):
        return True

    def is_sync(self):
        return True
