''' 
Path.py - A single movement from one point to another 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import numpy as np                                                          # Needed for sqrt
from numpy import linalg as la

class Path: 	
    ''' The axes of evil, the feed rate in mm/min and ABS or REL '''
    def __init__(self, axes, feed_rate, movement):
        self.axes = axes
        self.feed_rate = feed_rate
        self.movement = movement
        self.global_pos = {"X":0, "Y":0, "Z":0, "E":0} 
        self.actual_travel = axes.copy()
           
    ''' Set the next path element '''
    def set_next(self, next):
        self.next = next

    ''' Set the previous path element '''
    def set_prev(self, prev):
        self.prev = prev

    ''' Get the length of this path segment '''
    def get_length(self):      
        if "X" in self.axes:
            x = self.axes["X"]/1000.0
            if self.movement == "ABSOLUTE":
                x -= self.global_pos["X"]
        else:
            x = 0
        if "Y" in self.axes:
            y = self.axes["Y"]/1000.0
            if self.movement == "ABSOLUTE":        
                y -= self.global_pos["Y"]
        else:
            y = 0

        self.length = np.sqrt(x**2+y**2)                             # calculate the hypotenuse to the X-Y vectors, 

        if "Z" in self.axes:
            z = self.axes["Z"]/1000.0
            if self.movement == "ABSOLUTE":           
                z -= self.global_pos["Z"]
            self.length  = np.sqrt(self.length**2+z**2)                  # Also include the z-travel          

        return self.length

    ''' Get the length of the axis '''
    def get_axis_length(self, axis):
        if not axis in self.axes:
            return 0.0
        if self.movement == "ABSOLUTE":            
            return self.axes[axis]/1000.0 - self.global_pos[axis]     
        else:
            return self.axes[axis]/1000.0                         # If movement is relative, the vector is already ok. 

    ''' Get the top speed of this segment '''
    def get_max_speed(self):
        return (self.feed_rate/60.0)/1000.0

    ''' Get the ratio for this axis '''
    def get_axis_ratio(self, axis):
        hyp     = self.get_length()    	                                # Calculate the ratio               
        if hyp == 0.0:
            return 1.0
        return abs(self.get_axis_length(axis))/hyp

    ''' Get the lowest speed along this segment '''
    def get_end_speed(self):
        return (1-self.angle_to_next()/np.pi)*self.get_max_speed()

    ''' Get the lowest speed along this segment '''
    def get_start_speed(self):
        return (1-self.angle_to_prev()/np.pi)*self.get_max_speed()

    ''' Return the list of axes '''
    def get_axes(self):
        return self.axes

    ''' set the distance that was actually travelled.. '''
    def set_travelled_distance(self, axis, td):
        self.actual_travel[axis] = td

    ''' Return the actual travelled distance for this path '''
    def get_travelled_distance(self):
        return self.actual_travel

    ''' Set the global position for the printer '''
    def set_global_pos(self, global_pos):
        self.global_pos = global_pos

    ''' Return the angle to the next path segment '''
    def angle_to_next(self):
        if not hasattr(self, 'next'):
            return 0
        u = la.norm([self.get_axis_length("X"), self.get_axis_length("Y")])
        v = la.norm([self.next.get_axis_length("X"), self.next.get_axis_length("Y")])
        c = np.dot(u,v)/(u*v)
        angle = np.arccos(c)

        if np.isnan(angle):
            if (u == v).all():
                return 0.0
            else:
                return np.pi
        return angle

    ''' Return the angle to the previous path segment '''
    def angle_to_prev(self):
        if not hasattr(self, 'prev'):
            return 0
        u = la.norm([self.get_axis_length("X"), self.get_axis_length("Y")])
        v = la.norm([self.prev.get_axis_length("X"), self.prev.get_axis_length("Y")])
        c = np.dot(u,v)/(u*v)
        angle = np.arccos(c)

        if np.isnan(angle):
            if (u == v).all():
                return 0.0
            else:
                return np.pi
        return angle
        
        
if __name__ == '__main__':
    a = Path({"X": 10, "Y": 0}, 3000, "RELATIVE")
    b = Path({"X": -10, "Y": 0}, 3000, "RELATIVE")
    c = Path({"X": 0, "Y": 10}, 3000, "RELATIVE")
    
    b.set_next(c)
    b.set_prev(a)

    print "Max speed "+str(b.get_max_speed())
    print "Start speed "+str(b.get_start_speed())
    print "End speed "+str(b.get_end_speed())







