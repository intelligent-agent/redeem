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
    def __init__(self, axes, feed_rate, movement, is_print_segment=True):
        self.axes = axes
        self.feed_rate = feed_rate
        self.movement = movement
        self.global_pos = {"X":0, "Y":0, "Z":0, "E":0} 
        self.actual_travel = axes.copy()
        self.is_print_segment = is_print_segment         # If this is True, 
        self.axis_config = "H-belt"                      # If you need to do some sort of mapping, add the branch here. (ex scara arm)
          
    ''' Set the next path element '''
    def set_next(self, next):
        self.next = next

    ''' Set the previous path element '''
    def set_prev(self, prev):
        self.prev = prev
    
    def set_global_pos(self, global_pos, update_next = True):
        ''' Set the global position for the printer '''
        self.global_pos = global_pos		
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
        if "Z" in self.axes:
            z = self.axes["Z"]/1000.0
            if self.movement == "ABSOLUTE":           
                z -= self.global_pos["Z"]
        else:
            z = 0
        if "E" in self.axes:
            e = self.axes["E"]/1000.0
            if self.movement == "ABSOLUTE":           
                e -= self.global_pos["E"]
        else:
            e = 0

        # implement any transformation. Hipsterbot has an H-type belt, so: 
        # This was taken from the article "Dynamic modelling of a Two-axis, Parallel H-frame-Type XY Positioning System".
        if self.axis_config == "H-belt":
            A = np.matrix('-0.5 0.5; -0.5 -0.5')
            b = np.array([x, y])
            X = np.dot(np.linalg.inv(A), b)
            x = X[0, 0]
            y = X[0, 1]

        self.vector = {"X":x, "Y":y, "Z":z, "E":e}
    
        # Update the "probable" (as in not true) global pos of the next segment. 
        # This is in order to calculate the angle to it. Thus it need not be exact. 
        if hasattr(self, 'next'):
            a = self.global_pos
            b = self.vector
            # Do not continue the update beyond the bnext segment
            self.next.set_global_pos(dict( (n, a.get(n, 0)+b.get(n, 0)) for n in set(a)|set(b) ), False)
    
    ''' Get the length of this path segment '''
    def get_length(self):     
        x = self.vector["X"]
        y = self.vector["Y"]
        z = self.vector["Z"]
        self.length = np.sqrt(x**2+y**2+z**2)                             # calculate the hypotenuse to the X-Y vectors, 
        return self.length

    
    def get_axis_length(self, axis):
        ''' Get the length of the axis '''
        return self.vector[axis]

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
        return { k : v for k,v in self.vector.iteritems() if v != 0 }

    ''' set the distance that was actually travelled.. '''
    def set_travelled_distance(self, axis, td):
        self.actual_travel[axis] = td

    ''' Return the actual travelled distance for this path '''
    def get_travelled_distance(self):
        return self.actual_travel

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







