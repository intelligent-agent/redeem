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
import math
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
        self.arc_tolerance = 2E-6 # meters = 2 microns. TODO: FFF processes do not need this precision. Should probably be user configurable
        self.axis_0 = None
        self.axis_1 = None
        self.axis_linear = None

    def is_G92(self):
        """ Special path, only set the global position on this """
        return self.movement == Path.G92

    def set_arc_plane(self, axis_0, axis_1):
        self.axis_0 = axis_0
        self.axis_1 = axis_1

    def set_arc_linear(self, axis):
        self.axis_linear = axis

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

    def get_arc_segments(self): 
        # Based on optimized code from Grbl - https://github.com/grbl/grbl/blob/master/grbl/gcode.c
        # Parameter should first be validated sane, in gcode/G2_G3.py

        start_point = self.prev.ideal_end_pos
        end_point   = self.ideal_end_pos
        axis_0 = self.axis_0
        axis_1 = self.axis_1
        axis_linear = self.axis_linear
        is_clockwise_arc = True if self.movement == Path.G2 else False
   
        """
        Check if we can achieve the requested arc. From Grbl code comments ... 
            "[It is an error if] the radius to the current point and the radius to the
            target point differs more than 0.002mm (EMC def. 0.5mm OR 0.005mm and 0.1% radius)."
        """
        offset = np.array([
                self.axes.get('I',  0.0),
                self.axes.get('J',  0.0),
                self.axes.get('K',  0.0)
            ]) 
        d0 = end_point[axis_0] - start_point[axis_0] - offset[axis_0] # delta axis_0 between circle center and target
        d1 = end_point[axis_1] - start_point[axis_1] - offset[axis_1] # delta ax0s_1 between circle center and target
        target_r = math.sqrt(d0**2 + d1**2)
        radius = math.sqrt(offset[axis_0]**2 + offset[axis_1]**2) # between start_point and circle center
        delta_radius = abs(target_r - radius)
        if delta_radius > 0.005E-3:
            if delta_radius > 0.5E-3:
                logging.error("ARC definition error: >0.5mm (%fmm)", delta_radius/1000)
                return []
            if delta_radius > (0.001 * radius):
                logging.error("ARC definition error: > 0.005mm and 0.1% (%fmm)", delta_radius/1000)
                return []

        """
        Execute an arc in offset mode format. position == current xyz, target == target xyz, 
        offset == offset from current xyz, axis_X defines circle plane in tool space, axis_linear is
        the direction of helical travel, radius == circle radius, isclockwise boolean. Used
        for vector transformation direction.
        The arc is approximated by generating a huge number of tiny, linear segments. The chordal tolerance
        of each segment is configured in settings.arc_tolerance, which is defined to be the maximum normal
        distance from segment to the circle when the end points both lie on the circle.
        """
        center_axis0 = start_point[axis_0] + offset[axis_0] 
        center_axis1 = start_point[axis_1] + offset[axis_1]
        r_axis0 = -offset[axis_0]  # Radius vector from center to current location
        r_axis1 = -offset[axis_1]
        rt_axis0 = end_point[axis_0] - center_axis0
        rt_axis1 = end_point[axis_1] - center_axis1
             
        # CCW angle between position and target from circle center. Only one atan2() trig computation required.
        angular_travel = math.atan2(r_axis0 * rt_axis1 - r_axis1 * rt_axis0, r_axis0 * rt_axis0 + r_axis1 * rt_axis1);
        if is_clockwise_arc: # Correct atan2 output per direction
            if angular_travel >= -5.0E-7:
                angular_travel -= 2 * math.pi
        else:
            if angular_travel <= 5.0E-7:
                angular_travel += 2 * math.pi

        num_segments = int(
                math.floor( 
                    abs(0.5 * angular_travel * radius) 
                  / math.sqrt(self.arc_tolerance * ( 2 * radius - self.arc_tolerance))
                )
            )

        if num_segments > 0:

            theta_per_segment = angular_travel / num_segments
            linear_per_segment = (end_point[axis_linear] - start_point[axis_linear]) / num_segments

            """
            Vector rotation by transformation matrix: r is the original vector, r_T
            is the rotated vector, and phi is the angle of rotation. Solution
            approach by Jens Geisler.

                r_T = [cos(phi) -sin(phi);
                       sin(phi)  cos(phi)] * r
                                                                   
            For arc generation, the center of the circle is the axis of rotation
            and the radius vector is defined from the circle center to the initial
            position. Each line segment is formed by successive vector rotations.
            Single precision values can accumulate error greater than tool
            precision in rare cases.  So, exact arc path correction is implemented.
            This approach avoids the problem of too many very expensive trig
            operations [sin(),cos(),tan()] which can take 100-200 usec each to
            compute.
            ... [see grbl:motion_control.c for more]

            """

            cos_T = 1 - theta_per_segment**2 / 2
            sin_T = theta_per_segment - theta_per_segment**3 / 6
            
            # construct the arc from num_segments vectors
            path_segments = []
            segment = np.copy(start_point)
            count = 0
            for index in range(0, num_segments):
                """
                For a small performacne gain, we just rotate the previous
                vector three times, then correct any small drift on the forth
                """
                if (count < 4):
                    # Apply vector rotation matrix. ~40 usec
                    r_axisi = r_axis0 * sin_T + r_axis1 * cos_T
                    r_axis0 = r_axis0 * cos_T - r_axis1 * sin_T
                    r_axis1 = r_axisi
                    count += 1
                else:
                    """
                    Compute exact location by applying transformation matrix
                    from initial radius vector(=-offset)
                    """
                    cos_Ti = math.cos( (index+1) * theta_per_segment )
                    sin_Ti = math.sin( (index+1) * theta_per_segment )
                    r_axis0 = -offset[axis_0] * cos_Ti + offset[axis_1] * sin_Ti
                    r_axis1 = -offset[axis_0] * sin_Ti - offset[axis_1] * cos_Ti
                    count = 0

                segment[axis_0] = center_axis0 + r_axis0
                segment[axis_1] = center_axis1 + r_axis1
                segment[axis_linear] += linear_per_segment

                vector = dict(zip(self.printer.AXES, segment))
                path = AbsolutePath(vector, self.speed, self.accel, self.cancelable, self.use_bed_matrix, False)
                if index is not 0:
                    path.set_prev(path_segments[-1])
                else:
                    path.set_prev(self.prev)

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

