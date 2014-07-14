'''
Printer class holding all printer components

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from Path import Path

# A command received from pronterface or whatever
class Printer:

    def __init__(self, steppers={}, heaters={}, end_stops={},fans=[],cold_ends=[], path_planner=None):
        self.steppers=steppers
        self.heaters=heaters
        self.end_stops=end_stops
        self.fans=fans
        self.cold_ends=cold_ends
        self.path_planner=path_planner
        self.coolers = []

        self.comms = {} # Communication channels

        self.factor         = 1.0
        self.movement       = Path.ABSOLUTE
        self.feed_rate      = 0.5
        self.acceleration   = 0.5
        self.current_tool   = "E"

    ''' This method is callled for every move, so it should be fast/cached. '''
    def ensure_steppers_enabled(self):
        for name, stepper in self.steppers.iteritems():
            if stepper.in_use and not stepper.enabled: # Stepper should be enabled, but is not.
                stepper.set_enabled(True) # Force update

    ''' Send a reply through the proper channel '''
    def reply(self, gcode):
        if(gcode.get_answer()!=None):
            self.send_message(gcode.prot, gcode.get_answer())
    
    ''' Send a message back to host '''
    def send_message(self, prot, msg):
        self.comms[prot].send_message(msg)
