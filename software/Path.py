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
    matrix_H        = np.matrix('-0.5 0.5; -0.5 -0.5')    
    matrix_H_inv    = np.linalg.inv(matrix_H)                 

    # Precalculate the CoreXY matrix
    # TODO: This is the wrong transformation 
    matrix_XY       = np.matrix('-0.5 0.5; -0.5 -0.5')    
    matrix_XY_inv   = np.linalg.inv(matrix_XY)

    # Delta printer variables
    delta_R          = 0.2
    delta_Ls         = 0.1**2
    delta_Hcz        = 0.01

    e = 26.0
    f = 69.0
    re = 128.0
    rf = 88.0
 
    # Trigonometric constants
    s = 165*2
    sqrt3 = np.sqrt(3.0)
    sin120 = sqrt3 / 2.0
    cos120 = -0.5
    tan60 = sqrt3
    sin30 = 0.5
    tan30 = 1.0 / sqrt3

    axis_config = AXIS_CONFIG_XY # Default config is normal cartesian XY
    max_speeds  = np.ones(NUM_AXES)
    min_speed   = 0.005
    min_speeds  = np.ones(NUM_AXES)*0.005*0.57735026919
    
    home_speed  = np.ones(NUM_AXES)
    steps_pr_meter = np.ones(NUM_AXES)
    

    """ The axes of evil, the feed rate in m/s and ABS or REL """
    def __init__(self, axes, speed, acceleration, cancelable=False):
        self.axes               = axes
        self.speed              = speed
        self.acceleration       = acceleration
        self.cancelable        = int(cancelable)
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

    ''' Transform vector to whatever coordinate system is used '''
    def transform_vector(self, vec):
        ret_vec = np.copy(vec)
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:            
            X = np.dot(Path.matrix_H_inv, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY:            
            X = np.dot(Path.matrix_XY_inv, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_DELTA:         
            theta = [0, 0, 0]
            status = self.angle_yz(vec[0],vec[1],vec[2])
             
            if status[0] == 0:
                theta[0] = status[1]
                status = self.angle_yz(vec[0]*Path.cos120 + vec[1]*Path.sin120, 
                vec[1]*Path.cos120-vec[0]*Path.sin120,
                vec[2],
                theta[1])
            if status[0] == 0:
                theta[1] = status[1]
                status = self.angle_yz(vec[0]*Path.cos120 - vec[1]*Path.sin120,
                vec[1]*Path.cos120 + vec[0]*Path.sin120,
                vec[2],
                theta[2])            
            theta[2] = status[1]
            ret_vec[:3] = theta
        return ret_vec
        

    # Inverse kinematics
    # Helper functions, calculates angle theta1 (for YZ-pane)
    def angle_yz(self, x0, y0, z0, theta=None):
        y1 = -0.5*0.57735*Path.f # f/2 * tg 30
        y0 -= 0.5*0.57735*Path.e # shift center to edge
        # z = a + b*y
        a = (x0**2 + y0**2 + z0**2 + Path.rf**2 - Path.re**2 - y1**2) / (2.0*z0)
        b = (y1-y0) / z0
         
        # discriminant
        d = -(a + b*y1)*(a + b*y1) + Path.rf*(b**2*Path.rf + Path.rf)
        if d<0:
            return [1,0] # non-existing povar. return error, theta
         
        yj = (y1 - a*b - np.sqrt(d)) / (b*b + 1) # choosing outer povar
        zj = a + b*yj
        theta = np.arctan(-zj / (y1-yj)) * 180.0 / np.pi + (180.0 if yj>y1 else 0.0)
        
        return [0,theta] # return error, theta

    ''' Transform back from whatever '''
    def reverse_transform_vector(self, vec):
        ret_vec = np.copy(vec)
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:            
            X = np.dot(Path.matrix_H, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY:            
            X = np.dot(Path.matrix_XY, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_DELTA:    
            x0 = 0.0
            y0 = 0.0
            z0 = 0.0
            theta1 = vec[0]
            theta2 = vec[1]
            theta3 = vec[2]
    
            t = (Path.f-Path.e) * Path.tan30 / 2.0
            dtr = np.pi / 180.0
            theta1 *= dtr
            theta2 *= dtr
            theta3 *= dtr
            y1 = -(t + Path.rf*np.cos(theta1) )
            z1 = -Path.rf * np.sin(theta1)
            y2 = (t + Path.rf*np.cos(theta2)) * Path.sin30
            x2 = y2 * Path.tan60
            z2 = -Path.rf * np.sin(theta2)
            y3 = (t + Path.rf*np.cos(theta3)) * Path.sin30
            x3 = -y3 * Path.tan60
            z3 = -Path.rf * np.sin(theta3)
            dnm = (y2-y1)*x3 - (y3-y1)*x2
            w1 = y1*y1 + z1*z1
            w2 = x2*x2 + y2*y2 + z2*z2
            w3 = x3*x3 + y3*y3 + z3*z3

            # x = (a1*z + b1)/dnm
            a1 = (z2-z1)*(y3-y1) - (z3-z1)*(y2-y1)
            b1= -( (w2-w1)*(y3-y1) - (w3-w1)*(y2-y1) ) / 2.0

            # y = (a2*z + b2)/dnm
            a2 = -(z2-z1)*x3 + (z3-z1)*x2
            b2 = ( (w2-w1)*x3 - (w3-w1)*x2) / 2.0

            # a*z^2 + b*z + c = 0
            a = a1*a1 + a2*a2 + dnm*dnm
            b = 2.0 * (a1*b1 + a2*(b2 - y1*dnm) - z1*dnm*dnm)
            c = (b2 - y1*dnm)*(b2 - y1*dnm) + b1*b1 + dnm*dnm*(z1*z1 - Path.re**2)
            # discriminant
            d = b*b - 4.0*a*c
            if d < 0.0:
                return ret_vec # non-existing povar. return error,x,y,z
            z0 = -0.5*(b + np.sqrt(d)) / a
            x0 = (a1*z0 + b1) / dnm
            y0 = (a2*z0 + b2) / dnm
             
            ret_vec[:3] = [x0, y0, z0]

        return ret_vec

    ''' The vector representation of this path segment '''
    def __str__(self):
        return "Path from "+str(self.start_pos)+" to "+str(self.end_pos)

    @staticmethod
    def axis_to_index(axis):
        return Path.AXES.index(axis)


''' A path segment with absolute movement '''
class AbsolutePath(Path):

    def __init__(self, axes, speed, acceleration, cancelable=False):
        Path.__init__(self, axes, speed, acceleration, cancelable)
        self.movement = Path.ABSOLUTE

    ''' Set the previous path element '''
    def set_prev(self, prev):
        self.prev = prev
        self.start_pos = prev.end_pos
        
        # Make the start, end and path vectors. 
        self.end_pos = np.copy(self.start_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.end_pos[index] = self.axes[axis] 

        self.vec = self.end_pos - self.start_pos    

        # Compute stepper translation
        vec            = self.transform_vector(self.vec)
        num_steps      = np.ceil(np.abs(vec) * Path.steps_pr_meter)        
        self.delta     = np.sign(vec)*num_steps/Path.steps_pr_meter
        vec            = self.reverse_transform_vector(self.delta)

        # Set stepper and true posision
        self.end_pos            = self.start_pos + vec
        self.stepper_end_pos    = self.start_pos + self.delta

        prev.next = self
              

''' A path segment with Relative movement '''
class RelativePath(Path):

    def __init__(self, axes, speed, acceleration=0.5, cancelable=False):
        Path.__init__(self, axes, speed, acceleration, cancelable)
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

        # Compute stepper translation
        vec            = self.transform_vector(self.vec)
        num_steps      = np.ceil(np.abs(vec) * Path.steps_pr_meter)        
        stepper_vec    = np.sign(vec)*num_steps/Path.steps_pr_meter
        vec            = self.reverse_transform_vector(stepper_vec)

        # Set stepper and true posision
        self.end_pos            = self.start_pos + vec
        self.stepper_end_pos    = self.start_pos + stepper_vec


''' A reset axes path segment. No movement occurs, only global position setting '''
class G92Path(Path):
    
    def __init__(self, axes, speed, acceleration=0.5, cancelable=False):
        Path.__init__(self, axes, speed, acceleration, cancelable)
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



