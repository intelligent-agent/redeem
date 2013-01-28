''' 
Path.py - A single movement from one point to another 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import numpy as np                                                          # Needed for sqrt

class Path: 	
    ''' The axes of evil, the feed rate in mm/min and ABS or REL '''
    def __init__(self, axes, feed_rate, movement):
        axes["X"] = axes["X"]/1000.0 if "X" in axes else 0.0	            # Convert to SI-unit (meteres)
        axes["Y"] = axes["Y"]/1000.0 if "Y" in axes else 0.0
        axes["Z"] = axes["Z"]/1000.0 if "Z" in axes else 0.0
        axes["E"] = axes["E"]/1000.0 if "E" in axes else 0.0

        self.axes = axes
        self.feed_rate = feed_rate
        self.actual_travel = axes.copy()

        hyp = np.sqrt(axes["X"]**2+axes["Y"]**2)                             # calculate the hypotenuse to the X-Y vectors, 
        self.length  = np.sqrt(hyp**2+axes["Z"]**2)                          # Also include the z-travel          
            
    ''' Set the next path element '''
    def set_next(self, next):
        self.next = next

    ''' Set the previous path element '''
    def set_prev(self, prev):
        self.prev = prev
        
    ''' Get the length of this path '''
    def get_length(self):
        return self.length

    ''' Get the length of the axis '''
    def get_axis_length(self, axis):
        return self.axes[axis]

    ''' Calculate the angle this path has with another path '''
    def get_angle_with(self, next_path):
        raise Exception("Not implemented!")

    ''' Get the top speed of this segment '''
    def get_max_speed(self):
        return (self.feed_rate/60.0)/1000.0

    ''' Get the lowest speed along this segment '''
    def get_min_speed(self):
        return 0

    ''' Return the list of axes '''
    def get_axes(self):
        return self.axes

    ''' set the distance that was actually travelled.. '''
    def set_travelled_distance(self, axis, td):
        self.actual_travel[axis] = td
