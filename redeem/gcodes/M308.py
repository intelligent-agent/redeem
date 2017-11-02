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
from six import iteritems


class M308(GCodeCommand):

    def execute(self, g):
        # If no tokens are given, return the current settings    
        if g.num_tokens() == 0:
            g.set_answer("ok C: " + ' '.join('%s:%.1f mm' % (i[0], i[1]*1000) for i in sorted(
                iteritems(self.printer.path_planner.travel_length))))
        else:
            # Tokens are given, set the travel length for each token
            for axis, value in iteritems(g.get_tokens_as_dict()):
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
        return "Set or get direction and search length for end stops"

    def get_long_description(self):
        return ("Set or get direction and search length for end stops\n"
                "If not tokens are given, return the end stop travel search length in mm.\n"
                "If tokens are given, they must be a space separated list of <axis><value> pairs.\n"
                "Example: 'M308 X250 Y220'. This will set the travel search length for the \n"
                "X nd Y axis to 250 and 220 mm. Th values will appear in the config file in meters, "
                "thus 0.25 and 0.22")
