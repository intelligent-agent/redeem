'''
GCode T0 and T1
Select currently used extruder tool

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand

class T0(GCodeCommand):

    def execute(self,g):
        self.printer.current_tool = "E"

    def get_description(self):
        return "Select currently used extruder tool to be T0 (E)"

class T1(GCodeCommand):

    def execute(self,g):
        self.printer.current_tool = "H"

    def get_description(self):
        return "Select currently used extruder tool to be T1 (H)"