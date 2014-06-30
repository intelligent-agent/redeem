'''
GCode M119
Get current endstops state

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand


class M119(GCodeCommand):

    def execute(self, g):
        g.set_answer("ok "+", ".join([v.name+": "+str(int(v.hit)) for k,v in self.printer.end_stops.iteritems()]))

    def get_description(self):
        return "Get current endstops state"
