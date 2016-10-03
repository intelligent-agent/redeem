""" 
Path.py - A single movement from one point to another 
All coordinates  in this file is in meters.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
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
"""

import numpy as np
import logging

class Path:
    
    printer = None

    # Different types of paths
    ABSOLUTE = 0
    RELATIVE = 1
    MIXED = 2
    G92 = 3
    G2 = 4
    G3 = 5

    # Numpy array type used throughout    
    DTYPE = np.float64
    
    def __init__(self, axes, speed, accel, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        """ The axes of evil, the feed rate in m/s and ABS or REL """
        self.axes = axes
        self.speed = speed
        self.accel = accel
        self.cancelable = int(cancelable)
        self.use_bed_matrix = int(use_bed_matrix)
        self.use_backlash_compensation = int(use_backlash_compensation)
        self.enable_soft_endstops = enable_soft_endstops
        self.next = None
        self.prev = None
        self.speeds = None
        self.start_pos = None
        self.end_pos = None
        self.ideal_end_post = None
        

    def is_G92(self):
        """ Special path, only set the global position on this """
        return self.movement == Path.G92

    def set_homing_feedrate(self):
        """ The feed rate is set to the lowest axis in the set """
        self.speeds = np.minimum(self.speeds,
                                 self.home_speed[np.argmax(self.vec)])
        self.speed = np.linalg.norm(self.speeds[:3])

    def unlink(self):
        """ unlink this from the chain. """
        self.next = None
        self.prev = None

    @staticmethod
    def backlash_reset():
        #TODO: This needs further attention
        return

    def needs_splitting(self):
        #return False
        """ Return true if this is a radius """
        if self.movement == Path.G2 or self.movement == Path.G3:
            return True

    def get_segments(self):
        """ Returns split segments for delta or arcs """
        if self.movement == Path.G2 or self.movement == Path.G3:
            return self.get_arc_segments()

    def parametric_circle(self, t, xc, yc, R):
        x = xc + R*np.cos(t)
        y = yc + R*np.sin(t)
        return x,y

    def inv_parametric_circle(self, x, xc, R):
        t = np.arccos((x-xc)/R)
        return t
        

    def get_arc_segments(self):
        # The code in this function was taken from 
        # http://stackoverflow.com/questions/11331854/how-can-i-generate-an-arc-in-numpy
        start_point = self.prev.ideal_end_pos[:2]
        end_point   = self.ideal_end_pos[:2]

        i = self.I
        j = self.J

        # Find radius
        R = np.sqrt(i**2 + j**2)

        #logging.info(start_point)
        #logging.info(end_point)
        #logging.info(R)


        # Find start and end points
        start_t = self.inv_parametric_circle(start_point[0], start_point[0]+i, R)
        end_t   = self.inv_parametric_circle(end_point[0], start_point[0]+i, R)

        num_segments = np.ceil(np.abs(end_t-start_t)/self.split_size)+1


        # TODO: test this, it is probably wrong. 
        if self.movement == G2: 
            arc_T = np.linspace(start_t, end_t, num_segments)
        else:        
            arc_T = np.linspace(end_t, start_t, num_segments)
        X,Y = self.parametric_circle(arc_T, start_point[0]+i, start_point[1]+j, R)
    
        #logging.info([X, Y])
        
        # Interpolate the remaining values
        vals = np.transpose([
                    np.linspace(
                        self.prev.ideal_end_pos[i], 
                        self.ideal_end_pos[i], 
                        num_segments
                        ) for i in xrange(self.printer.MAX_AXES)]) 

        # Update the X and Y positions
        for i, val in enumerate(vals):
            val[:2] = (X[i], Y[i])
        vals = np.delete(vals, 0, axis=0)

        vec_segments = [dict(zip(self.printer.axes_zipped, list(val))) for val in vals]
        path_segments = []

        for index, segment in enumerate(vec_segments):
            #print segment
            path = AbsolutePath(segment, self.speed, self.accel, self.cancelable, self.use_bed_matrix, False) #
            if index is not 0:
                path.set_prev(path_segments[-1])
            else:
                path.set_prev(self.prev)
            path_segments.append(path)

        #for seg in path_segments:
        #    logging.info(seg)
 
        return path_segments

    def __str__(self):
        """ The vector representation of this path segment """
        return "Path from " + str(self.start_pos[:4]) + " to " + str(self.end_pos[:4])

class AbsolutePath(Path):
    """ A path segment with absolute movement """
    def __init__(self, axes, speed, accel, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        Path.__init__(self, axes, speed, accel, cancelable, use_bed_matrix, use_backlash_compensation, enable_soft_endstops)
        self.movement = Path.ABSOLUTE

    def set_prev(self, prev):
        """ Set the previous path element """
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos

        # Make the start, end and path vectors. 
        self.ideal_end_pos = np.copy(prev.ideal_end_pos)
        for index, axis in enumerate(self.printer.AXES):
            if axis in self.axes:
                self.ideal_end_pos[index] = self.axes[axis]
    
        # Store the ideal end pos, so the target 
        # coordinates are pushed forward
        self.end_pos = np.copy(self.ideal_end_pos)
        if self.use_bed_matrix:
            self.end_pos[:3] = self.end_pos[:3].dot(self.printer.matrix_bed_comp)

        #logging.debug("Abs before: "+str(self.ideal_end_pos[:3])+" after: "+str(self.end_pos[:3]))
        
class RelativePath(Path):
    """ 
    A path segment with Relative movement 
    This is an approximate relative movement, i.e. we will move according to:
      (where we actually are) -> (somewhere close to = (where we think we are + our passed in vector))
      but it should be pretty close!
    """
    def __init__(self, axes, speed, accel, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        Path.__init__(self, axes, speed, accel, cancelable, use_bed_matrix, use_backlash_compensation, enable_soft_endstops)
        self.movement = Path.RELATIVE

    def set_prev(self, prev):
        """ Link to previous segment """
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos

        # Generate the vector
        vec = np.zeros(self.printer.MAX_AXES, dtype=Path.DTYPE)
        for index, axis in enumerate(self.printer.AXES):
            if axis in self.axes:
                vec[index] = self.axes[axis]

        # Calculate the ideal end position. 
        # In an ideal world, this is where we want to go. 
        self.ideal_end_pos = np.copy(prev.ideal_end_pos) + vec
        
        self.end_pos = self.start_pos + vec
        

class MixedPath(Path):
    """ A path some mixed and some absolute movement axes """
    def __init__(self, axes, speed, accel, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        Path.__init__(self, axes, speed, accel, cancelable, use_bed_matrix, use_backlash_compensation, enable_soft_endstops)
        self.movement = Path.MIXED

    def set_prev(self, prev):
        """ Set the previous path element """
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos

        # Make the start, end and path vectors. 
        self.ideal_end_pos = np.copy(prev.ideal_end_pos)
        for axis in self.axes:
            index = self.printer.axis_to_index(axis)
            if (axis in self.printer.axes_relative):
                self.ideal_end_pos[index] += self.axes[axis]
            elif (axis in self.printer.axes_absolute):
                self.ideal_end_pos[index] = self.axes[axis]

        # Store the ideal end pos, so the target 
        # coordinates are pushed forward
        self.end_pos = np.copy(self.ideal_end_pos)
        if self.use_bed_matrix:
            self.end_pos[:3] = self.end_pos[:3].dot(self.printer.matrix_bed_comp)



class G92Path(Path):
    """ A reset axes path segment. No movement occurs, only global position
    setting """
    def __init__(self, axes, cancelable=False, use_bed_matrix=False):
        Path.__init__(self, axes, 0, 0, cancelable, use_bed_matrix)
        self.movement = Path.G92


    def set_prev(self, prev):
        """ Set the previous segment """
        self.prev = prev
        if prev is not None:
            self.start_pos      = prev.end_pos
            self.end_pos        = np.copy(self.start_pos) 
            self.ideal_end_pos  = np.copy(prev.ideal_end_pos)
            prev.next = self
        else:
            self.start_pos      = np.zeros(self.printer.MAX_AXES, dtype=Path.DTYPE)
            self.end_pos        = np.zeros(self.printer.MAX_AXES, dtype=Path.DTYPE)
            self.ideal_end_pos  = np.zeros(self.printer.MAX_AXES, dtype=Path.DTYPE)

        # Update the ideal pos based on G92 values
        for index, axis in enumerate(self.printer.AXES):
            if axis in self.axes:
                self.ideal_end_pos[index] = self.axes[axis]
                self.end_pos[index] = self.axes[axis]

        # Update the matrix compensated pos
        if self.use_bed_matrix:
            matrix_pos = np.copy(self.ideal_end_pos)
            matrix_pos[:3] = matrix_pos[:3].dot(self.printer.matrix_bed_comp)
            for index, axis in enumerate(self.printer.AXES):
                if axis in self.axes:
                    self.end_pos[index] = matrix_pos[index]
        #logging.debug("G92 before: "+str(self.ideal_end_pos[:3])+" after: "+str(self.end_pos[:3]))

