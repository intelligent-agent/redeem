"""
GCode M202 & M201  - set acceleration

Author: Boris Lasic
email: boris(at)max(dot)si
Website: http://www.max.si
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from redeem.Path import Path
except ImportError:
    from Path import Path


class M201(GCodeCommand):

    def execute(self, g):

        t = self.printer.acceleration[:];
      
        for i in range(g.num_tokens()):
            axis = Path.axis_to_index(g.token_letter(i))
            t[axis] = float(g.token_value(i)) / 3600.0

        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY or Path.axis_config == Path.AXIS_CONFIG_H_BELT:
            # x and y should have same accelerations for lines to be straight
            t[1] = t[0] 
        elif Path.axis_config == Path.AXIS_CONFIG_DELTA:
            # Delta should have same accelerations on all axis
            t[1] = t[0]
            t[2] = t[0]

        # Setup 3d movement accel
        self.set_acceleration(tuple(t[:3]))

        # Setup the extruder accel
        for i in range(Path.NUM_AXES - 3):
            e = self.printer.path_planner.native_planner.getExtruder(i)
            self.set_extruder_acceleration(e,t[i + 3])

              
    
    def get_description(self):
        return ("Sets the acceleration that axes can do in units/second^2 for print moves." 
               " For consistency with the rest of G Code movement " 
                "this should be in units/(minute^2) Example: M201 X1000 Y1000 Z100 E2000")

    def is_buffered(self):
        return False

    def set_acceleration(self, t):
        self.printer.path_planner.native_planner.setPrintAcceleration(t)

    def set_extruder_acceleration(self, e, accel):
        e.setPrintAcceleration(accel)
    



class M202(M201):
    def set_acceleration(self, t):
        self.printer.path_planner.native_planner.setTravelAcceleration(t)

    def set_extruder_acceleration(self,e, accel):
        # We do nothing for the extruder for travel moves
        pass 

    def get_description(self):
        return ("Sets the acceleration that axes can do in units/second^2 for travel moves." 
               " For consistency with the rest of G Code movement " 
                "this should be in units/(minute^2) Example: M201 X1000 Y1000 Z100 E2000")
 
