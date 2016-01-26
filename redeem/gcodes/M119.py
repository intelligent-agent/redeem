"""
GCode M119
Get current endstops state

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand


class M119(GCodeCommand):
    def execute(self, g):
        # Todo: implement ability to ivert endstops on the fly. 
        #if g.has_letter("P") and g.has_letter("S"):
        #    name = g.get_value_by_letter("P") # X1, X2, Y1, Y2 etc. 
        #    if name in self.printer.end_stops:
        #        self.printer.end_stops[name].set_inverted(bool(g.get_value_by_letter("S")))
        #    else:
        #        logging.warning("M119: Non-existing end-stop name "+str(name))
        #else:
        g.set_answer("ok "+", ".join([v.name+": "+str(int(v.hit)) for k,v in self.printer.end_stops.iteritems()]))

    def get_description(self):
        return "Get current endstops state"
