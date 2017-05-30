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
    G92 = 2
    G2 = 3
    G3 = 4

    # Numpy array type used throughout    
    DTYPE = np.float64

    # http://www.manufacturinget.org/2011/12/cnc-g-code-g17-g18-and-g19/
    X_Y_ARC_PLANE = 0
    X_Z_ARC_PLANE = 1
    Y_Z_ARC_PLANE = 2

    # max length of any segment in an arc
    ARC_SEGMENT_LENGTH = 0.1 / 1000
    
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
        """ Return true if this is a arc movement"""
        return self.movement == Path.G2 or self.movement == Path.G3

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

    def get_plane_coordinates(self, pos):
        """ Returns the two points in the arc plane """
        if self.printer.arc_plane == Path.X_Y_ARC_PLANE:
            return pos[0], pos[1]
        if self.printer.arc_plane == Path.X_Z_ARC_PLANE:
            return pos[0], pos[2]
        # Path.Y_Z_ARC_PLANE
        return pos[1], pos[2]

    def get_plane_location(self, pos):
        """ Returns the arc plane position """
        if self.printer.arc_plane == Path.X_Y_ARC_PLANE:
            return pos[2]
        if self.printer.arc_plane == Path.X_Z_ARC_PLANE:
            return pos[1]
        # Path.Y_Z_ARC_PLANE
        return pos[0]

    def get_arc_coordinates(self, point):
        """ Creates a coordinate given a point and the plane location """
        if self.printer.arc_plane == Path.X_Y_ARC_PLANE:
            return {'X': point[0], 'Y': point[1]}
        if self.printer.arc_plane == Path.X_Z_ARC_PLANE:
            return {'X': point[0], 'Z': point[1]}
        # Path.Y_Z_ARC_PLANE
        return {'Y': point[0], 'Z': point[1]}

    def get_offset(self):
        if self.printer.arc_plane == Path.X_Y_ARC_PLANE:
            return self.I, self.J
        if self.printer.arc_plane == Path.X_Z_ARC_PLANE:
            return self.I, self.K
        # Path.Y_Z_ARC_PLANE
        return self.J, self.K

    def get_distance(self, pointA, pointB):
        return np.sqrt( (pointB[1]-pointA[1])**2 + (pointB[0]-pointA[1])**2 )

    def get_arc_segments(self):

        # references:
        #  - http://stackoverflow.com/questions/11331854/how-can-i-generate-an-arc-in-numpy
        #  - http://www.manufacturinget.org/2011/12/cnc-g-code-g02-and-g03/

        # points on the arc plane
        start_point = self.get_plane_coordinates(self.prev.ideal_end_pos)
        end_point = self.get_plane_coordinates(self.ideal_end_pos)
        plane_location = self.get_plane_location(self.ideal_end_pos)

        # center offset from start point on the arc plane
        offset = self.get_offset()

        radius = np.sqrt(offset[0]**2 + offset[1]**2)

        logging.info("start point: {}".format(start_point))
        logging.info("offset: {}".format(offset))
        logging.info("end point: {}".format(end_point))
        logging.info("radius: {}".format(radius))

        # Find start and end tangent vectors
        start_t = self.inv_parametric_circle(start_point[0], offset[0], radius)
        end_t = self.inv_parametric_circle(end_point[0], offset[0], radius)

        # number of segments based on 
        arc_length = np.pi * radius * np.arctan(self.get_distance(start_point, end_point) / radius)
        num_segments = np.ceil(arc_length / self.ARC_SEGMENT_LENGTH)

        # calculate arc tangent vectors
        if self.movement == Path.G2:
            arc_T = np.linspace(start_t, end_t, num_segments)
        else:        
            arc_T = np.linspace(end_t, start_t, num_segments)

        # create plane point pairs (either X/Y, X/Z or Y/Z)
        X, Y = self.parametric_circle(arc_T, start_point[0]+offset[0], start_point[1]+offset[1], radius)

        path_segments = []

        for index, segment in enumerate(zip(X, Y)):
            segment_end = self.get_arc_coordinates(segment)
            logging.info("segment: {}".format(segment_end))
            path = AbsolutePath(segment_end, self.speed, self.accel, self.cancelable, self.use_bed_matrix, False)
            if index is not 0:
                path.set_prev(path_segments[-1])
            else:
                path.set_prev(self.prev)

            logging.info("path segment: {}".format(path))
            path_segments.append(path)

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

