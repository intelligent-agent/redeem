'''
GCode G90 and G91
Set movement mode to absolute or relative

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand

class G90(GCodeCommand):

    def execute(self,g):
        self.printer.movement = "ABSOLUTE"


    def get_description(self):
        return "Set movement mode to absolute"

class G91(GCodeCommand):

    def execute(self,g):
        self.printer.movement = "RELATIVE"


    def get_description(self):
        return "Set movement mode to relative"
