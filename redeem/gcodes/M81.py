"""
GCode M81
Shutdown the whole Replicape controller board

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import os


class M81(GCodeCommand):

    def execute(self, g):
        if g.has_letter("P"):         
            g.answer = None   # Prevent reply
            self.printer.redeem.running = False
            self.printer.path_planner.queue_sync_event(True)
        elif g.has_letter("R"):
            g.answer = None   # Prevent reply
            os.system("systemctl restart redeem")
        else:
            os.system("shutdown -h now")

    def get_description(self):
        return "Shutdown the whole Replicape controller board. If paramter P is present, only exit loop. If R is present, restart daemon"

    def is_buffered(self):
        return False
