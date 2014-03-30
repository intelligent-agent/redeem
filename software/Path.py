""" 
Path.py - A single movement from one point to another 
All coordinates  in this file is in meters. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/



"""

import numpy as np                                                          # Needed for sqrt
from numpy import linalg as la
import ConfigParser
import logging

class Path: 	
    AXES                = "XYZEHABC"
    NUM_AXES            = 5#len(AXES)

    AXIS_CONFIG_XY      = 0
    AXIS_CONFIG_H_BELT  = 1
    AXIS_CONFIG_CORE_XY = 2
    AXIS_CONFIG_DELTA   = 3

    ABSOLUTE            = 0
    RELATIVE            = 1
    G92                 = 2

    # Numpy array type used throughout    
    DTYPE               = np.float32

    # Precalculate the H-belt matrix
    A = np.matrix('-0.5 0.5; -0.5 -0.5')    
    Ainv = np.linalg.inv(A)                 

    axis_config = AXIS_CONFIG_XY # Default config is normal cartesian XY
    max_speed   = np.ones(NUM_AXES)
    home_speed  = np.ones(NUM_AXES)

    """ The axes of evil, the feed rate in m/s and ABS or REL """
    def __init__(self, axes, speed, movement,  acceleration=0.5, cancellable=False):
        self.axes               = axes
        self.speed              = speed
        self.acceleration       = acceleration
        self.movement           = movement
        self.cancellable        = int(cancellable)
        self.start_speed        = 0.0
        self.end_speed          = 0.0
        self.mag                = None
        self.next               = None

    """ Set the previous path element """

    # TODO: Must calculate the speed for each of the axes individually. 
    # Start speed must match end speed
    # Also, remember axistransformations
    def set_prev(self, prev):
        self.prev = prev
        if prev != None:
            self.start_pos = prev.end_pos
            prev.next = self
        else:
            self.start_pos = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)
        
        if self.movement == Path.ABSOLUTE:
            # Make the start, end and path vectors. 
            self.end_pos = np.copy(self.start_pos)
            for index, axis in enumerate(Path.AXES):
                if axis in self.axes:
                    self.end_pos[index] = self.axes[axis] 
            self.vec = self.end_pos - self.start_pos            
            self.abs_vec = np.abs(self.vec)
            self.hyp     = self.get_magnitude()
            self.ratios  = self.abs_vec/self.hyp
            self.speeds  = self.speed*self.ratios
            self.accelerations = self.acceleration*self.ratios

            # Calculate the angle to prev
            if prev:
                self.angle_to_prev = self._angle_between(prev.vec, self.vec)
                self.prev.angle_to_next = self.angle_to_prev  # Direction is not important (or is it...?)

                if self.angle_to_prev > np.pi/2.0:
                    # We have discovered a segment with too steep angle. The end speed of the 
                    # Previous segments until a start sement is discovered must be updated. 
                    self.is_start_segment    = True 
                    self.is_end_segment      = False
                    self.start_speeds        = np.zeros(Path.NUM_AXES)
                    self.angle_speeds        = np.zeros(Path.NUM_AXES)
                    self.accel_speeds        = np.sqrt(2.0*self.accelerations*self.abs_vec)
                    self.decel_speeds        = np.zeros(Path.NUM_AXES)
                    # We assume that max speed is not reached, 
                    self.end_speeds           = np.minimum(self.accel_speeds, self.speeds)
                    # We now have a section with start speed and end speed of zero 
                    # so a accelleration profile can be generated. 
                    self.prev.is_end_segment = True
                    self.prev.end_speeds     = np.zeros(Path.NUM_AXES)
                    self.prev.calculate_deceleration()
                else:
                     # We have an angle that can be cornered at > 0 speed. 
                    self.is_start_segment = False
                    self.is_end_segment   = False
                    self.angle_speeds     = self.speeds * self.angle_to_ratio(self.angle_to_prev)
                    self.accel_speeds     = np.sqrt(np.square(self.prev.start_speeds) + 2.0*self.accelerations*self.abs_vec)
                    self.start_speeds     = np.minimum(self.angle_speeds, self.prev.end_speeds)
                    self.prev.end_speeds  = self.start_speeds
                    self.end_speeds       = np.sqrt(np.square(self.start_speeds) + 2.0*self.accelerations*self.abs_vec)
            else:
                # This is the first known segment in the print. 
                self.is_start_segment   = True
                self.is_end_segment     = False
                self.start_speeds       = np.zeros(Path.NUM_AXES)
                self.angle_speeds       = np.zeros(Path.NUM_AXES)
                self.accel_speeds       = np.sqrt(2.0*self.accelerations*self.abs_vec)
            
        elif self.movement == Path.RELATIVE:
            logging.debug("Relative")
            self.vec = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)
            for index, axis in enumerate(Path.AXES):
                if axis in self.axes:
                    self.vec[index] = self.axes[axis] 
            self.end_pos = self.start_pos + self.vec
            self.abs_vec = np.abs(self.vec)
            self.hyp     = self.get_magnitude()
            self.ratios  = self.abs_vec/self.hyp
            self.speeds  = self.speed*self.ratios
            self.accelerations = self.acceleration*self.ratios

            # Start and stop speeds are set to zero 
            self.is_start_segment   = True
            self.is_end_segment     = True
            self.start_speeds       = np.zeros(Path.NUM_AXES)
            self.end_speeds         = np.zeros(Path.NUM_AXES)

    ''' This path segment is the last in the print or whatever '''
    def finalize(self):
        self.is_end_segment = True
        self.end_speeds = np.zeros(Path.NUM_AXES)
        self.calculate_deceleration()

    ''' Given an angle in radians, return the speed ratio '''
    def angle_to_ratio(self, angle):
        return (1-angle/np.pi)
    
    """ Special path, only set the global position on this """
    def is_G92(self):
        return (self.movement == Path.G92)

    ''' The feed rate is set to the lowest axis in the set '''
    def set_homing_feedrate(self):
        self.speed = min(self.speed, self.home_speed[np.argmax(vec)])

    ''' Recursively recalculate the decelleration profile '''
    def calculate_deceleration(self):
        if self.next: 
            self.decel_speeds = np.sqrt(np.square(self.next.end_speeds)+2.0*self.accelerations*self.abs_vec)
        else:
            self.decel_speeds = np.sqrt(2.0*self.accelerations*self.abs_vec)
        #self.start_speeds = np.minimum(self.start_speeds, self.decel_speeds)                
        if not self.is_start_segment:
            self.prev.calculate_deceleration()
        
    @staticmethod
    def speed_from_distance(s, a, V0=0):
        if V0:
            return np.sqrt(np.square(V0)+2.0*a*s)
        return np.sqrt(2.0*a*s)

    def end_speed_from_distance(self, s):
        return np.sqrt(2.0*self.acceleration*s)

    """ Set the global position for the printer """
    def set_global_pos(self, global_pos, update_next = True):
        
        # implement any transformation. Hipsterbot has an H-type belt, so: 
        # This was taken from the article "Dynamic modelling of a Two-axis, Parallel H-frame-Type XY Positioning System".
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:            
            b = np.array([x, y])
            X = np.dot(Path.Ainv, b)
            self.vector = {"X":X[0, 0], "Y":X[0, 1], "Z":z, "E":e, "H": h}

    """ Get the length of the XYZ dimentison this path segment """
    def get_magnitude(self):   
        if self.mag: 
            return self.mag
        self.mag = np.sqrt(self.vec[:3].dot(self.vec[:3]))
        return self.mag

    """ Get the ratio for this axis """
    def get_axis_ratio(self, axis_nr):
        hyp     = self.get_magnitude()    	                               
        if hyp == 0.0: # Single axis
            return 1.0
        return abs(self.vec[axis_nr])/hyp

    ''' unlink this from the chain. '''
    def unlink(self):
        self.next = None
        self.prev = None

    def unit_vector(self, vector):
        return vector / np.linalg.norm(vector)        

    """ Returns the angle in radians between vectors 'v1' and 'v2':: Creds to David Wolever for this """
    def _angle_between(self, v1, v2):
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        angle = np.arccos(np.dot(v1_u, v2_u))
        if np.isnan(angle):
            if (v1_u == v2_u).all():
                return 0.0
            else:
                return np.pi
        return angle

       
    """ Give a steppers position, return the position along the axis """
    def stepper_to_axis(self, pos, axis):
        if axis == "X":
            if Path.axis_config == Path.AXIS_CONFIG_H_BELT:
                X = np.array([pos, 0])
                b = np.dot(Path.A, X)
                return tuple(np.array(b)[0])
            else:
                return (pos, 0.0)
        if axis == "Y":
            if Path.axis_config == Path.AXIS_CONFIG_H_BELT:
                X = np.array([0, pos])
                b = np.dot(Path.A, X)
                return tuple(np.array(b)[0])
            else:
                return (0.0, pos)
		
        # For all other axes, return the same value
        return pos

    ''' Make the acceleration profiles '''
    def split_into_axes(self):
        logging.debug("Split into axies")
        # Find the length of the acceleration segment       
        tm_start = (self.speeds-self.start_speeds)/self.accelerations
        self.max_speed_starts = self.start_speeds*tm_start + 0.5*self.accelerations*tm_start**2
        
        # Calculate the time for when max speed is met. 
        tm_end   = (self.speeds-self.start_speeds)/self.accelerations
        self.max_speed_ends = self.end_speeds*tm_end + 0.5*self.accelerations*tm_end**2

        # Find the point of switch  
        self.switch = (2*self.accelerations*self.abs_vec-np.square(self.start_speeds)+np.square(self.end_speeds))/(4*self.accelerations)


    @staticmethod
    def axis_to_index(axis):
        return Path.AXES.index(axis)

    ''' The vector representation of this path segment '''
    def __str__(self):
        return "Vec. "+str(self.vec)


if __name__ == '__main__':
    global_pos = np.array([0, 0, 0, 0, 0])

    # Add path segment A. None before, none after
    a = Path({"X": 0.1, "Y": 0.0}, 0.3, Path.ABSOLUTE)
    a.set_prev(None)
    print "A: "+str(a)

    # Add path segment B. Make prev point to A. Make next of A point to B. 
    b = Path({"X": 0.1, "Y": 0.1}, 0.3, Path.ABSOLUTE)
    b.set_prev(a)
    print "B: "+str(b)

    # Add path segment C. Make pre of C point to B and next of B point to C. 
    c = Path({"X": 0.0, "Y": 0.1}, 0.3, Path.ABSOLUTE)
    c.set_prev(b)
    print "C: "+str(c)

    # Add path segment C. Make pre of C point to B and next of B point to C. 
    d = Path({"Y": -0.1}, 0.3, Path.RELATIVE)
    d.set_prev(c)
    print "D: "+str(d)

    # Now we want to know the stuff. 
    print "b.angle_to_next is "+str(b.angle_to_next())+" it should be pi/2 "
    print "b.angle_to_prev is "+str(b.angle_to_prev())+" is should be pi/2 "

    print "Max speed "+str(b.get_max_speed())
    print "Start speed "+str(b.get_start_speed())
    print "End speed "+str(b.get_end_speed())







