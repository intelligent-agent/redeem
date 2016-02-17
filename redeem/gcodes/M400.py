"""
GCode M400
Wait until all buffered paths are executed

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M400(GCodeCommand):

    def execute(self, g):

        # This needs to be a standard method somewhere
        if not self.printer.path_planner.queue_sync_event(False):    # No blocking of the PRU, (notification only)
            self.printer.path_planner.wait_until_done()              # The move buffer is already empty! fallback to this to ensure we're in sync.
            self.printer.sync_commands.task_done()                   # We should be at the front of the line.
            self.on_sync(g)                                          # Complete execution

    def on_sync(self, g):
        # self.printer.path_planner.clear_sync_event()  # Only needed if blocking the PRU
        self.readyEvent.set()                           # This is REQUIRED for synchronous commands!

    def get_description(self):
        return "Wait until all buffered paths are executed"

    def is_buffered(self):
        return True

    def is_sync(self):
        return True

