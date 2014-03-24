'''
Printer class holding all printer components

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

# A command received from pronterface or whatever
class Printer:

    def __init__(self, steppers={}, heaters={}, end_stops={},fans=[],cold_ends=[], path_planner=None):
        self.steppers=steppers
        self.heaters=heaters
        self.end_stops=end_stops
        self.fans=fans
        self.cold_ends=cold_ends

        self.path_planner=path_planner

        self.movement = "RELATIVE"
        self.feed_rate = 3000.0   
        self.current_tool="E"



