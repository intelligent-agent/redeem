'''
Printer class holding all printer components

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
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
