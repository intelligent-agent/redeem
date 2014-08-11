'''
GCode G4
Dwell

Author: Elias Bakken
email: elias dot bakken at gmail dot com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
from Path import Path, RelativePath, AbsolutePath
import logging
import time

class G4(GCodeCommand):

    def execute(self,g):
        self.printer.path_planner.wait_until_done()
        if g.has_letter("P"): # Milliseconds
            sleep = float(g.get_value_by_letter("P"))/1000.0
        if g.has_letter("S"): # Seconds
            sleep = float(g.get_value_by_letter("S"))
        time.sleep(sleep)

    def get_description(self):
        return "Dwell for P(milliseconds) or S (seconds)"

    def is_buffered(self):
        return True
