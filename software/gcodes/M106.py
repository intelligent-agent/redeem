'''
GCode cM106
Control fans

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from AbstractGcode import AbstractGcode

# A command received from pronterface or whatever
class M106(AbstractGcode):

    def __init__(self, printer):
        self.printer=printer


    def execute(self,gcode):
        fan_no = gcode.get_int_by_letter("P", 0)               
        value = float(gcode.get_int_by_letter("S", 255))/255.0
        fan = self.printer.fans[fan_no]
        fan.set_value(value)

        return "OK"
