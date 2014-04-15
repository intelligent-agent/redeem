'''
GCode M92
Set number of steps per millimeters for each steppers

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand
from Stepper import Stepper

class M92(GCodeCommand):

    def execute(self,g):
        for i in range(g.num_tokens()):                          # Run through all tokens
            axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
            self.printer.steppers[axis].set_steps_pr_mm(float(g.token_value(i)))        
        Stepper.commit() 

    def get_description(self):
        return "Set number of steps per millimeters for each steppers"
