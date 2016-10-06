"""
GCode M308
Set travel direction and distance

Author: Elias Bakken
email: elias(at)iagent(dot)no
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging

class M308(GCodeCommand):

    def execute(self, g):
        # If no tokens are given, return the current settings    
        if g.num_tokens() == 0:
            g.set_answer("ok C: " + ' '.join('%s:%.1f mm' % (i[0], i[1]*1000) for i in sorted(
                self.printer.path_planner.travel_length.iteritems())))
        else:
            # Tokens are given, set the travel length for each token
            for axis, value in g.get_tokens_as_dict().iteritems():
                if axis in self.printer.path_planner.travel_length:
                    try:
                        fvalue = float(value)/1000.0
                        logging.debug("Setting travel for axis {} to {} mm".format(axis, value))
                        self.printer.path_planner.travel_length[axis] = fvalue
                    except ValueError:
                         logging.error("Unable to convert value to float for axis {}: {}".format(axis, value))
                else:
                    logging.warning("Axis does not exis: {}".format(axis))
                
        
    def get_description(self):
        return "Set or get the direction and length to search for end stops"

    def get_long_description(self):
        return ("Set P, I and D values, Format (M301 E0 P0.1 I100.0 D5.0)"
                "P = Kp, default = 0.0"
                "I = Ti, default = 0.0"
                "D = Td, default = 0.0"
                "E = Extruder, -1=Bed, 0=E, 1=H, 2=A, 3=B, 4=C, default = 0")
