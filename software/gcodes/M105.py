'''
GCode M104
Get extruder temperature

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from GCodeCommand import GCodeCommand

class M105(GCodeCommand):

    def execute(self,g):
        answer = "ok T:"+str(self.printer.heaters['E'].get_temperature())
        if "HBP" in self.printer.heaters:
            answer += " B:"+str(int(self.printer.heaters['HBP'].get_temperature()))
        if "H" in self.printer.heaters:
            answer += " T1:"+str(int(self.printer.heaters['H'].get_temperature()))
        if len(self.printer.cold_ends)>0:
            answer += " T2:"+str(int(self.printer.cold_ends[0].get_temperature())) 
   
        g.set_answer(answer)  

    def get_description(self):
        return "Get extruder temperature"
