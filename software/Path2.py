""" 
Path.py - A single movement from one point to another 
All coordinates  in this file is in meters. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/



"""

import numpy as np                                                          # Needed for sqrt
import ConfigParser
import logging

class Path:     
    AXES                = "XYZEH"
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
    max_speeds  = np.ones(NUM_AXES)
    min_speed   = 0.005
    min_speeds  = np.ones(NUM_AXES)*0.005*0.57735026919
    
    home_speed  = np.ones(NUM_AXES)
    steps_pr_meter = np.ones(NUM_AXES)
    

    """ The axes of evil, the feed rate in m/s and ABS or REL """
    def __init__(self, axes, speed, acceleration, cancellable=False):
        self.axes               = axes
        self.speed              = speed
        self.acceleration       = acceleration
        self.cancellable        = int(cancellable)
        self.mag                = None
        self.pru_data = []
        self.next               = None

    
    """ Special path, only set the global position on this """
    def is_G92(self):
        return (self.movement == Path.G92)

    ''' The feed rate is set to the lowest axis in the set '''
    def set_homing_feedrate(self):
        self.speeds = np.minimum(self.speeds, self.home_speed[np.argmax(self.vec)])
        self.speed = np.linalg.norm(self.speeds[:3])

    ''' unlink this from the chain. '''
    def unlink(self):
        self.next = None
        self.prev = None


    ''' The vector representation of this path segment '''
    def __str__(self):
        return "Path from "+str(self.start_pos)+" to "+str(self.end_pos)


''' A path segment with absolute movement '''
class AbsolutePath(Path):

    def __init__(self, axes, speed, acceleration, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.ABSOLUTE

    ''' Set the previous path element '''
    # TODO: Must calculate the speed for each of the axes individually. 
    # Start speed must match end speed
    # Find the controlling axis and use that for calculating the other axes. 
    def set_prev(self, prev):
        self.prev = prev


        self.start_pos = prev.end_pos

        
        # Make the start, end and path vectors. 
        self.end_pos = np.copy(self.start_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.end_pos[index] = self.axes[axis] 

        
        prev.next = self
              

''' A path segment with Relative movement '''
class RelativePath(Path):

    def __init__(self, axes, speed, acceleration=0.5, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.RELATIVE

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

        self.end_pos    = self.start_pos + self.vec
        


''' A reset axes path segment. No movement occurs, only global position setting '''
class G92Path(Path):
    
    def __init__(self, axes, speed, acceleration=0.5, cancellable=False):
        Path.__init__(self, axes, speed, acceleration, cancellable)
        self.movement = Path.G92
        self.ratios = np.ones(Path.NUM_AXES)

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



