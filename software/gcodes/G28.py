'''
GCode G28
Steppers homing

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
import logging

class G28(GCodeCommand):

    def execute(self,g):
        if g.num_tokens() == 0:                                  # If no token is given, home all
            g.set_tokens(["X0", "Y0", "Z0"])                
        self.printer.path_planner.wait_until_done()                                               # All steppers 
        for i in range(g.num_tokens()): # Run through all tokens
            axis = g.token_letter(i)                         
            if self.config.getboolean('Endstops', 'has_'+axis.lower()):
                self.printer.path_planner.home(axis)     
        self._send_message(g.prot, "Homing done.")
        logging.info("Homing done.")


    def get_description(self):
        return "Move the steppers to their homing position (and find it as well)"
