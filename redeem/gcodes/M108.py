"""
GCode M108
Break out of a wait loop. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html
"""

from GCodeCommand import GCodeCommand

class M108(GCodeCommand):

    def execute(self, g):
        self.printer.running_M116 = False

    def get_description(self):
        return "Break out of any running M116 loop"
        
    def is_buffered(self):
        return True
