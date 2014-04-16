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
    AXES                = "XYZEH"#ABC
    NUM_AXES            = len(AXES)

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
    min_speed   = np.ones(NUM_AXES)*0.005
    home_speed  = np.ones(NUM_AXES)
    steps_pr_meter = np.ones(NUM_AXES)
    

    """ The axes of evil, the feed rate in m/s and ABS or REL """
    def __init__(self, axes, speed, acceleration=0.5, cancellable=False):
        self.axes               = axes
        self.speed              = speed
        self.acceleration       = acceleration
        self.cancellable        = int(cancellable)
        self.start_speed        = 0.0
        self.end_speed          = 0.0
        self.mag                = None
        self.next               = None
        self.is_added           = False
        self.is_start_segment   = False
        self.is_end_segment     = False

    ''' Transform vector to whatever coordinate system is used '''
    def transform_vector(self, vec):
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:            
            X = np.dot(Path.Ainv, self.vec[0:2])
            vec[0:2] = X[0]
        # TODO: Implement CoreXY and Delta 
        return vec
        
    ''' Transform back from whatever '''
    def reverse_transform_vector(self, vec):
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:            
            X = np.dot(Path.A, self.vec[0:2])
            vec[0:2] = X[0]
        # TODO: Implement CoreXY and Delta 
        return vec

    ''' Use the steps pr meter to conver tto actual travelled distance '''
    def vector_to_stepper_translation(self, vec):
        vec = self.transform_vector(vec)
        self.num_steps       = np.round(np.abs(vec) * Path.steps_pr_meter)        
        #logging.debug("num steps set: "+str(vec)+" "+str(self.num_steps))
        self.stepper_vec = np.sign(vec)*self.num_steps/Path.steps_pr_meter
        vec = self.reverse_transform_vector(self.stepper_vec)
        return vec

    ''' Find the controlling axis '''
    def find_controlling_axis(self, vec):
        return np.argmax(vec[0:3])
    
    ''' Given an angle in radians, return the speed ratio '''
    def angle_to_ratio(self, angle):
        return (1-angle/np.pi)
    
    """ Special path, only set the global position on this """
    def is_G92(self):
        return (self.movement == Path.G92)

    ''' The feed rate is set to the lowest axis in the set '''
    def set_homing_feedrate(self):
        self.speeds = np.minimum(self.speeds, self.home_speed[np.argmax(vec)])

    """ Get the length of the XYZ dimentison this path segment """
    def get_magnitude(self):   
        if self.mag: 
            return self.mag
        self.mag = np.sqrt(self.vec[:3].dot(self.vec[:3]))
        return self.mag

    ''' Get hypotenuse of the traversal '''
    def get_hyp(self):
        hyp     = self.get_magnitude()    	                               
        if hyp == 0.0: # Single axis
            return 1.0
        return hyp

    ''' Get the ratios of the '''
    def get_ratios(self):
        self.hyp     = self.get_hyp()
                        
        if self.hyp != 1.0:
            self.ratios  = self.abs_vec/self.hyp
        else:
            self.ratios = np.ones(Path.NUM_AXES)

        return self.ratios

    ''' unlink this from the chain. '''
    def unlink(self):
        self.next = None
        self.prev = None



    ''' G92 and Relative does not need to calculate decelleration '''
    def calculate_deceleration(self):
        logging.debug("Skipping decel-calc on G92 or Relative")
        pass

    @staticmethod
    def unit_vector(vector):
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else vector*0.0

    """ Returns the angle in radians between vectors 'v1' and 'v2':: Creds to David Wolever for this """
    @staticmethod 
    def angle_between(v1, v2):
        v1_u = Path.unit_vector(v1)
        v2_u = Path.unit_vector(v2)
        angle = np.arccos(np.dot(v1_u, v2_u))
        if np.isnan(angle):
            if (v1_u == v2_u).all():
                return 0.0
            else:
                return np.pi
        return angle

    @staticmethod
    def axis_to_index(axis):
        return Path.AXES.index(axis)

    @staticmethod
    def speed_from_distance(s, a, V0):
        return np.sqrt(np.square(V0)+2.0*a*s)
    
    @staticmethod
    def acceleration_from_distance(s, V0, V1):
        return np.divide((np.square(V1)-np.square(V0)), (2*s))

    @staticmethod
    def distance_from_acceleration(a, V0, V1):
         return (np.square(V1)-np.square(V0))/(2.0*a)
    
    @staticmethod
    def distance_from_speed(a, V0, V1):
         return (np.square(V1)-np.square(V0))/(2.0*a)
    
    @staticmethod
    def ratio_from_angle(angle):
        return (1.0-angle/np.pi)

    ''' The vector representation of this path segment '''
    def __str__(self):
        return "Vec. "+str(self.vec)


''' A path segment with absolute movement '''
class AbsolutePath(Path):

    def __init__(self, axes, speed, acceleration=0.1, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.ABSOLUTE

    ''' Set the previous path element '''
    # TODO: Must calculate the speed for each of the axes individually. 
    # Start speed must match end speed
    # Find the controlling axis and use that for calculating the other axes. 
    def set_prev(self, prev):
        self.prev = prev
        self.start_pos = prev.end_pos
        prev.next = self
              
        # Make the start, end and path vectors. 
        self.end_pos = np.copy(self.start_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.end_pos[index] = self.axes[axis] 
        self.vec = self.end_pos - self.start_pos    
        # Convert to actual traveled distance by the steppers
        self.vec = self.vector_to_stepper_translation(self.vec)
        self.end_pos = self.start_pos + self.vec
        self.abs_vec = np.abs(self.vec)
        self.ratios = self.get_ratios()
        self.speeds = self.speed*self.ratios

        # Calculate the angle to previous path segment
        self.angle_to_prev = Path.angle_between(prev.vec[:3], self.vec[:3])

        #logging.debug("Angle: "+str(self.angle_to_prev))

        if self.angle_to_prev > np.pi/2.0:
           
            # We have discovered a segment with too steep angle. The end speed of the 
            # Previous segments until a start sement is discovered must be updated. 
            self.is_start_segment    = True 
            self.start_speeds        = Path.min_speed*self.ratios
            self.start_speed         = np.linalg.norm(self.start_speeds[:3])

            # We now have a section with start speed and end speed of zero 
            # so a accelleration profile can be generated. 
            self.prev.is_end_segment = True
            self.prev.end_speeds     = Path.min_speed*self.prev.ratios
            self.prev.calculate_deceleration()
        else:
            # We have an angle that can be cornered at > 0 speed.                 
            angle_ratio = self.ratio_from_angle(self.angle_to_prev)
            # The newly discovered angle will cause a speed decrease. 
            # If the new speed is below the old, update it. 
            if self.prev.end_speed > self.prev.speed*angle_ratio:
                #logging.debug("Applying angle speed "+str(angle_ratio))
                self.prev.end_speed  = self.prev.speed*angle_ratio
                self.prev.end_speeds = self.prev.ratios*self.prev.end_speed
            self.start_speeds       = self.prev.end_speeds

        # Calculate the end speed based on the previous segment
        self.start_speed = np.linalg.norm(self.start_speeds[:3])
        self.accel_speed = Path.speed_from_distance(self.mag, self.acceleration, self.start_speed)

        # Clip the end speed             
        if self.accel_speed > self.speed:
            self.end_speed = self.speed
        else:
            self.end_speed = self.accel_speed
            
        self.end_speeds = self.ratios*self.end_speed
        #self.max_speed_ends = Path.distance_from_acceleration(self.accelerations, self.start_speeds, self.end_speeds)
        #print "vec = "+str(self.vec[:2])
        #print "Start speeds = "+str(self.start_speeds[:2])
        #print "End speeds   = "+str(self.end_speeds[:2])        

    ''' This path segment is the last in the print or whatever '''
    def finalize(self):
        self.is_end_segment = True
        self.end_speeds = Path.min_speed*self.ratios
        self.end_speed = np.linalg.norm(self.end_speeds[:3])
        self.calculate_deceleration()

    ''' Recursively recalculate the decelleration profile '''
    def calculate_deceleration(self):
        if self.next:
            self.end_speed = self.next.start_speed
            self.end_speeds = self.next.start_speeds
        
        self.decel_speed = Path.speed_from_distance(self.mag, self.acceleration, self.end_speed)
            
        #logging.debug("Calculate decel for vec "+str(self.vec))
        #logging.debug("start = "+str(self.start_speed))
        #logging.debug("end = "+str(self.end_speed))
        #logging.debug("decel = "+str(self.decel_speed))
        #logging.debug("acceleration = "+str(self.acceleration))
        
        # If the start speed is too high, adjust it
        if self.decel_speed < self.start_speed:
            #logging.debug("pure-decel")
            self.profile        = "pure-decel"
            self.start_speed    = self.decel_speed
            self.start_speeds   = self.start_speed*self.ratios
            self.max_speeds     = self.start_speeds
            self.accelerations  = np.zeros(Path.NUM_AXES)
            self.decelerations  = Path.acceleration_from_distance(self.abs_vec, self.start_speeds, self.end_speeds)
        elif abs(self.end_speed-self.accel_speed) < 0.00001: # Eliminate rounding error
            #logging.debug("pure-accel")
            self.profile        = "pure-accel"
            self.start_speeds   = self.start_speed*self.ratios
            self.max_speeds     = self.end_speeds
            self.accelerations  = Path.acceleration_from_distance(self.abs_vec, self.start_speeds, self.end_speeds)
            self.decelerations  = np.zeros(Path.NUM_AXES)
        else:
            # If we accelerate to a certain point, then decellerate, fint out where. 
            switch = (2*self.acceleration*self.mag-np.square(self.start_speed)+np.square(self.end_speed))/(4*self.acceleration)
            #switch = min(max(0, switch), self.mag)
            #logging.debug("switch = "+str(switch)+" of "+str(self.mag))
            max_speed = Path.speed_from_distance(switch, self.acceleration, self.start_speed)
            if max_speed < self.speed:
                # We accelerate to a certain point, then decellerate, never hitting the speed limit
                #logging.debug("accel-decel")
                self.profile        = "accel-decel"
                self.max_speeds     = max_speed*self.ratios
                # Find out where the switch occurs 
                max_dists           = self.ratios*switch            
                self.accelerations  = Path.acceleration_from_distance(max_dists, self.start_speeds, self.max_speeds)                
                self.decelerations  = Path.acceleration_from_distance(self.abs_vec-max_dists, self.end_speeds, self.max_speeds)
                #print self.decelerations
            else:
                # We hit the speed limit.
                #logging.debug("cruise")
                self.profile = "cruise"
                self.max_speeds     = self.speeds
                #logging.debug("Start speeds = "+str(self.start_speed))
                #logging.debug("Max   speeds = "+str(self.speed))
                #logging.debug("End   speeds = "+str(self.end_speed))
                # If all speeds are equal, accelerate through the segment
                if abs(self.start_speed - self.speed) < 0.0001 or abs(self.speed - self.end_speed) < 0.0001:
                    self.accelerations  = Path.acceleration_from_distance(self.abs_vec, self.start_speeds, self.end_speeds)
                    self.decelerations  = np.zeros(Path.NUM_AXES)
                else:
                    # Find out where max speed is hit
                    max_dists           = self.ratios*Path.distance_from_speed(self.acceleration, self.start_speed, self.speed)            
                    self.accelerations  = Path.acceleration_from_distance(max_dists, self.start_speeds, self.max_speeds)
                    # Find out where decelleration starts
                    end_dists           = self.ratios*Path.distance_from_speed(self.acceleration, self.end_speed, self.speed)                            
                    self.decelerations  = Path.acceleration_from_distance(end_dists, self.end_speeds, self.max_speeds)
                    #logging.debug("max dists = "+str(max_dists))
                    #logging.debug("end dists = "+str(end_dists))
        
        if not self.is_start_segment and self.prev:
            self.prev.calculate_deceleration()

''' A path segment with Relative movement '''
class RelativePath(Path):

    def __init__(self, axes, speed, acceleration=0.5, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.RELATIVE
        self.is_start_segment   = True
        self.is_end_segment     = True

    ''' Link to previous segment '''
    def set_prev(self, prev):
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos
               
        # Generate the vector 
        self.vec = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.vec[index] = self.axes[axis] 
        # Convert to actual traveled distance by the steppers
        self.vec        = self.vector_to_stepper_translation(self.vec)
        self.end_pos    = self.start_pos + self.vec
        self.abs_vec    = np.abs(self.vec)
        self.ratios     = self.get_ratios()
        self.speeds     = self.speed*self.ratios
        # Since speed, v_start and v_end are all in proportion to the segment length, a is also
        self.accelerations = self.acceleration*self.ratios
        self.decelerations = self.accelerations

        # Start and stop speeds are set to min
        self.start_speeds       = Path.min_speed*self.ratios
        self.end_speeds         = Path.min_speed*self.ratios
        self.start_speed        = np.linalg.norm(self.start_speeds[:3])
        # Calculate the speed reached half way
        self.accel_speed        = Path.speed_from_distance(self.mag/2, self.acceleration, self.start_speed)
        self.max_speed          = min(self.accel_speed, self.speed) 
        self.max_speeds         = self.max_speed*self.ratios

        self.profile = "relative"


''' A reset axes path segment. No movement occurs, only global position setting '''
class G92Path(Path):
    
    def __init__(self, axes, speed, acceleration=0.5, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.G92
        self.ratios = np.ones(Path.NUM_AXES)
        self.is_start_segment   = True
        self.is_end_segment     = True

    ''' Set the previous segment '''
    def set_prev(self, prev):
        self.prev = prev
        if prev != None:
            self.start_pos = prev.end_pos
            prev.next = self
        else:
            self.start_pos = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)

        self.end_pos = np.copy(self.start_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.end_pos[index] = self.axes[axis]
        self.vec = np.zeros(Path.NUM_AXES)

        # Start and End speed is used by the previous and folloing segments
        self.start_speeds       = Path.min_speed
        self.end_speeds         = Path.min_speed

        # End the previous segments path
        # FIXME: Must check if the previous segment is already calculated
        if self.prev != None:
            self.prev.calculate_deceleration()
        
    ''' G92 does not need to calculate decelleration '''
    def calculate_deceleration(self):
        logging.debug("Skipping decel-calc on G92")
        pass

if __name__ == '__main__':
    global_pos = np.array([0, 0, 0, 0, 0])

    # Allways start by adding a G92 path to reset all axes
    prev = G92Path({"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}, 0)
    prev.set_prev(None)

    # Add path segment A. None before, none after
    a = AbsolutePath({"X": 0.1, "Y": 0.0}, 0.1, 0.3)
    a.set_prev(prev)
    print "A: "+str(a)

    # Add path segment B. Make prev point to A. Make next of A point to B. 
    b = AbsolutePath({"X": 0.1, "Y": 0.1}, 0.1, 0.3)
    b.set_prev(a)
    print "B: "+str(b)

    # Add path segment C. Make pre of C point to B and next of B point to C. 
    c = AbsolutePath({"X": 0.0, "Y": 0.1}, 0.1, 0.3)
    c.set_prev(b)
    print "C: "+str(c)

    # Add path segment C. Make pre of C point to B and next of B point to C. 
    d = RelativePath({"Y": -0.1}, 0.1, 0.3)
    d.set_prev(c)
    print "D: "+str(d)

    # Now we want to know the stuff. 
    print "b.angle_to_next is "+str(b.angle_to_next)+" it should be pi/2 "
    print "b.angle_to_prev is "+str(a.angle_to_next)+" is should be pi/2 "

    print "Max speed "+str(b.speed)
    print "Start speed "+str(b.start_speed)
    print "End speed "+str(b.end_speed)


    




