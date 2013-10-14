""" 
Path.py - A single movement from one point to another 
All coordinates  in this file is in meters. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
"""

import numpy as np                                                          # Needed for sqrt
from numpy import linalg as la
import ConfigParser
import logging

AXIS_CONFIG_XY     = 0
AXIS_CONFIG_H_BELT = 1


class Path: 	
    A = np.matrix('-0.5 0.5; -0.5 -0.5')
    Ainv = np.linalg.inv(A)
    axis_config=AXIS_CONFIG_XY # Default config is normal cartesian XY
    max_speed_x = 1.0
    max_speed_y = 1.0
    max_speed_z = 1.0
    max_speed_e = 1.0
    max_speed_h = 1.0

    def __init__(self, axes, feed_rate, movement, is_print_segment=True):
        """ The axes of evil, the feed rate in m/s and ABS or REL """
        self.axes = axes
        self.feed_rate = feed_rate
        self.movement = movement
        self.global_pos = {"X":0, "Y":0, "Z":0, "E":0} 
        self.is_print_segment = is_print_segment         # If this is True, use angle stuff
        self.next_ok = False

    def is_G92(self):
        """ Special path, only set the global position on this """
        return (self.movement == "G92")
  
    def get_pos(self):
        return self.axes

    def set_next(self, next):
        """ Set the next path element """
        self.next = next

    def set_prev(self, prev):
        """ Set the previous path element """
        self.prev = prev

    def unlink(self):
        self.next = None
        self.prev = None
    
    def set_global_pos(self, global_pos, update_next = True):
        """ Set the global position for the printer """
        self.global_pos = global_pos 
        if "X" in self.axes:
            x = self.axes["X"]
            if self.movement == "ABSOLUTE":
                x -= self.global_pos["X"]

            self.feed_rate = min(self.feed_rate, Path.max_speed_x)
        else:
            x = 0
        if "Y" in self.axes:
            y = self.axes["Y"]
            if self.movement == "ABSOLUTE":        
                y -= self.global_pos["Y"]
            self.feed_rate = min(self.feed_rate, Path.max_speed_y) # Clamp the speed
        else:
            y = 0
        if "Z" in self.axes:
            z = self.axes["Z"]
            if self.movement == "ABSOLUTE":           
                z -= self.global_pos["Z"]            
            self.feed_rate = min(self.feed_rate, Path.max_speed_z)
        else:
            z = 0
        if "E" in self.axes:
            e = self.axes["E"]
            if self.movement == "ABSOLUTE":  
                e -= self.global_pos["E"]
            self.feed_rate = min(self.feed_rate, Path.max_speed_e)
        else:
            e = 0

        if "H" in self.axes:
            h = self.axes["H"]
            if self.movement == "ABSOLUTE":  
                h -= self.global_pos["H"]
            self.feed_rate = min(self.feed_rate, Path.max_speed_h)
        else:
            h = 0
        
        self.vector = {"X":x, "Y":y, "Z":z, "E":e, "H": h} 
        self.cartesian_vector = {"X":x, "Y":y, "Z":z, "E":e, "H": h} 
        
        logging.debug(self.vector)

        # Update the "probable" (as in not true) global pos of the next segment. 
        # This is in order to calculate the angle to it. Thus it need not be exact. 
        if hasattr(self, 'next') and update_next:
            a = self.global_pos
            b = self.cartesian_vector
            # Do not continue the update beyond the next segment
            self.next.set_global_pos(dict( (n, a.get(n, 0)+b.get(n, 0)) for n in set(a)|set(b) ), False)
            self.next_ok = True

        # implement any transformation. Hipsterbot has an H-type belt, so: 
        # This was taken from the article "Dynamic modelling of a Two-axis, Parallel H-frame-Type XY Positioning System".
        if Path.axis_config == AXIS_CONFIG_H_BELT:            
            b = np.array([x, y])
            X = np.dot(Path.Ainv, b)
            self.vector = {"X":X[0, 0], "Y":X[0, 1], "Z":z, "E":e, "H": h}

    def get_length(self):     
        """ Get the length of this path segment """
        x = self.vector["X"]
        y = self.vector["Y"]
        z = self.vector["Z"]
        self.length = np.sqrt(x**2+y**2+z**2)                             # calculate the hypotenuse to the X-Y vectors, 
        return self.length

    def get_axis_length(self, axis):
        """ Get the length of the axis """
        return self.vector[axis]

    def get_max_speed(self):
        """ Get the top speed of this segment """
        return self.feed_rate

    def get_axis_ratio(self, axis):
        """ Get the ratio for this axis """
        hyp     = self.get_length()    	                                # Calculate the ratio               
        if hyp == 0.0:
            return 1.0
        return abs(self.get_axis_length(axis))/hyp

    def get_start_speed(self):
        """ Get the lowest speed along this segment """
        return (1-self.angle_to_prev()/np.pi)*self.get_max_speed()

    def get_end_speed(self):
        """ Get the lowest speed along this segment """
        return (1-self.angle_to_next()/np.pi)*self.get_max_speed()

    def get_axes(self):
        """ Return the list of axes """
        return { k : v for k,v in self.vector.iteritems() if v != 0 }

    def unit_vector(self, vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector)        

    def angle_between(self, v1, v2):
        """ Returns the angle in radians between vectors 'v1' and 'v2':: Creds to David Wolever for this """
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        angle = np.arccos(np.dot(v1_u, v2_u))
        if np.isnan(angle):
            if (v1_u == v2_u).all():
                return 0.0
            else:
                return np.pi
        return angle
    
    def angle_to_next(self):
        """ Return the angle to the next path segment """
        if hasattr(self, 'angle_to_next_cal'):
            return self.angle_to_next_cal
        if self.next_ok == False:
            return 0

        v1 = [self.get_axis_length("X"), self.get_axis_length("Y")]
        v2 = [self.next.get_axis_length("X"), self.next.get_axis_length("Y")]
        angle = self.angle_between(v1, v2)
        self.angle_to_next_cal = angle
        return angle
    
    def angle_to_prev(self):
        """ Return the angle to the previous path segment """
        if hasattr(self, 'angle_to_prev_cal'):
            return self.angle_to_prev_cal
        if not hasattr(self, 'prev'):
            return 0

        v1 = [self.get_axis_length("X"), self.get_axis_length("Y")]
        v2 = [self.prev.get_axis_length("X"), self.prev.get_axis_length("Y")]
        angle = self.angle_between(v1, v2)
        self.angle_to_prev_cal = angle
        return angle
        
    def stepper_to_axis(self, pos, axis):
        """ Give a steppers position, return the position along the axis """
        if axis == "X":
            if Path.axis_config == AXIS_CONFIG_H_BELT:
                X = np.array([pos, 0])
                b = np.dot(Path.A, X)
                return tuple(np.array(b)[0])
            else:
                return (pos, 0.0)
        if axis == "Y":
            if Path.axis_config == AXIS_CONFIG_H_BELT:
                X = np.array([0, pos])
                b = np.dot(Path.A, X)
                return tuple(np.array(b)[0])
            else:
                return (0.0, pos)
		
        # For all other axes, return the same value
        return pos

    def is_type_print_segment(self): 
        """ Returns true if this is a print segment and not a relative move """
        return self.is_print_segment

if __name__ == '__main__':
    # Add path segment A. None before, none after
    a = Path({"X": 0.1, "Y": 0}, 0.3, "ABSOLUTE")

    # Add path segment B. Make prev point to A. Make next of A point to B. 
    b = Path({"X": 0.1, "Y": 0.1}, 0.3, "ABSOLUTE")
    b.set_prev(a)
    a.set_next(b)

    # Add path segment C. Make pre of C point to B and next of B point to C. 
    c = Path({"X": 0.0, "Y": 0.1}, 0.3, "ABSOLUTE")
    c.set_prev(b)
    b.set_next(c)

    # A is fetched and executed. 
    a.set_global_pos({"X": 0, "Y": 0}) 
    # B is fetched. 
    b.set_global_pos({"X": 0.1, "Y": 0}) 

    # Now we want to know the stuff. 
    print "Angle to next is "+str(b.angle_to_next())+" it should be pi/2 "
    print "Angle to prev is "+str(b.angle_to_prev())+" is should be pi/2 "

    print "Max speed "+str(b.get_max_speed())
    print "Start speed "+str(b.get_start_speed())
    print "End speed "+str(b.get_end_speed())







