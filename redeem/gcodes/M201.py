"""
GCode M202 & M201  - set acceleration

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
import logging


class M201(GCodeCommand):

    def execute(self, g):

        t = self.printer.acceleration[:];
      
        for i in range(g.num_tokens()):
            axis = self.printer.axis_to_index(g.token_letter(i))
            t[axis] = float(g.token_value(i)) / 3600.0

        if self.printer.axis_config == self.printer.AXIS_CONFIG_CORE_XY or self.printer.axis_config == self.printer.AXIS_CONFIG_H_BELT:
            # x and y should have same accelerations for lines to be straight
            t[1] = t[0] 
        elif self.printer.axis_config == self.printer.AXIS_CONFIG_DELTA:
            # Delta should have same accelerations on all axis
            t[1] = t[0]
            t[2] = t[0]
            
        logging.debug("M201: acceleration = "+str(t))
            
        self.printer.path_planner.native_planner.setAcceleration(t)

    def get_description(self):
        return "Set print acceleration"
    
    def get_long_description(self):
        return ("Sets the acceleration that axes can do in units/second^2 for print moves." 
               " For consistency with the rest of G Code movement " 
                "this should be in units/(minute^2) Example: M201 X1000 Y1000 Z100 E2000")

    def is_buffered(self):
        return False
    
 
