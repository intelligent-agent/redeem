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

from Delta import Delta
from BedCompensation import BedCompensation
import logging

class Path:
    AXES = "XYZEHABC"

    AXIS_CONFIG_XY = 0
    AXIS_CONFIG_H_BELT = 1
    AXIS_CONFIG_CORE_XY = 2
    AXIS_CONFIG_DELTA = 3

    ABSOLUTE = 0
    RELATIVE = 1
    G92 = 2

    # Numpy array type used throughout    
    DTYPE = np.float64

    # Precalculate the H-belt matrix
    matrix_H = np.matrix('-0.5 0.5; -0.5 -0.5')
    matrix_H_inv = np.linalg.inv(matrix_H)

    # Precalculate the CoreXY matrix
    # A - motor X (top right), B - motor Y (top left)
    # home located in bottom right corner    
    matrix_XY = np.matrix('1.0 1.0; 1.0 -1.0')
    matrix_XY_inv = np.linalg.inv(matrix_XY)

    # Unlevel bed compensation. 
    matrix_bed_comp     = np.identity(3)
    matrix_bed_comp_inv = np.linalg.inv(matrix_bed_comp)

    axis_config = AXIS_CONFIG_XY # Default config is normal cartesian XY

    @staticmethod
    def set_axes(num_axes):
        """ Set number of axes """
        Path.NUM_AXES = num_axes
        Path.max_speeds = np.ones(num_axes)
        Path.home_speed = np.ones(num_axes)
        Path.home_backoff_speed = np.ones(num_axes)
        Path.home_backoff_offset = np.zeros(num_axes)
        Path.steps_pr_meter = np.ones(num_axes)
        Path.backlash_compensation = np.zeros(num_axes)
        Path.backlash_state = np.zeros(num_axes)
        Path.soft_min = -np.ones(num_axes)*1000.0
        Path.soft_max = np.ones(num_axes)*1000.0

    def __init__(self, axes, speed,  cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        """ The axes of evil, the feed rate in m/s and ABS or REL """
        self.axes = axes
        self.speed = speed
        self.cancelable = int(cancelable)
        self.use_bed_matrix = int(use_bed_matrix)
        self.use_backlash_compensation = int(use_backlash_compensation)
        self.enable_soft_endstops = enable_soft_endstops
        self.mag = None
        self.pru_data = []
        self.next = None
        self.prev = None
        self.speeds = None
        self.vec = None
        self.start_pos = None
        self.end_pos = None
        self.stepper_end_pos = None
        self.ideal_end_pos = None
        self.num_steps = None
        self.delta = None
        self.compensation = None
        self.split_size = 0.001

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

    def transform_vector(self, vec, cur_pos):
        """ Transform vector to whatever coordinate system is used """
        ret_vec = np.copy(vec)
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:
            X = np.dot(Path.matrix_H_inv, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY:
            X = np.dot(Path.matrix_XY, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_DELTA:
            # Subtract the current column positions
            if hasattr(self.prev, "end_ABC"):
                self.start_ABC = self.prev.end_ABC
            else:
                self.start_ABC = Delta.inverse_kinematics2(cur_pos[0], cur_pos[1],
                                                 cur_pos[2])
            # Find the next column positions
            self.end_ABC = Delta.inverse_kinematics2(cur_pos[0] + vec[0],
                                               cur_pos[1] + vec[1],
                                               cur_pos[2] + vec[2])
            ret_vec[:3] = self.end_ABC - self.start_ABC

        # Apply Automatic bed compensation
        if self.use_bed_matrix:
            ret_vec[:3] = np.dot(Path.matrix_bed_comp, ret_vec[:3])
        return ret_vec

    def reverse_transform_vector(self, vec, cur_pos):
        """ Transform back from whatever """
        ret_vec = np.copy(vec)
        if Path.axis_config == Path.AXIS_CONFIG_H_BELT:
            X = np.dot(Path.matrix_H, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY:
            X = np.dot(Path.matrix_XY_inv, vec[0:2])
            ret_vec[:2] = X[0]
        if Path.axis_config == Path.AXIS_CONFIG_DELTA:
            # Find the next column positions
            self.end_ABC = self.start_ABC + vec[:3]

            # We have the column translations and need to find what that
            # represents in cartesian.
            start_xyz = Delta.forward_kinematics2(self.start_ABC[0], self.start_ABC[1],
                                                 self.start_ABC[2])
            end_xyz = Delta.forward_kinematics2(self.end_ABC[0], self.end_ABC[1],
                                               self.end_ABC[2])
            ret_vec[:3] = end_xyz - start_xyz

        # Apply Automatic bed compensation
        if self.use_bed_matrix:
            ret_vec[:3] = np.dot(Path.matrix_bed_comp_inv, ret_vec[:3])

        return ret_vec

    @staticmethod
    def backlash_reset():
	Path.backlash_state = np.zeros(Path.NUM_AXES)

    def backlash_compensate(self):
        """ Apply compensation to the distance taken if the direction of the axis has changed. """
        ret_vec = np.zeros(Path.NUM_AXES)
        if self.use_backlash_compensation:
            for index, d in enumerate(self.delta):
                dirstate = np.sign(d)
                #Compensate only if the direction has changed
                if (dirstate != 0) and (dirstate != Path.backlash_state[index]):
                    ret_vec[index] = dirstate * Path.backlash_compensation[index]
                    # Save new backlash state
                    Path.backlash_state[index] = dirstate

            if np.any(ret_vec):
                self.compensation = ret_vec;

        return ret_vec

    def needs_splitting(self):
        """ Return true if this is a delta segment and longer than 1 mm """
        return (Path.axis_config == Path.AXIS_CONFIG_DELTA 
            and self.get_magnitude() > self.split_size
            and np.any(self.vec[:2])) # If there is no movement along the XY axis (Z+extruders) only, don't split.

    def get_magnitude(self):
        """ Returns the magnitde in XYZ dim """
        if not self.mag:
            if self.rounded_vec == None:
                logging.error("Cannot get magnitude of vector without knowing its length")
            self.mag = np.linalg.norm(self.rounded_vec[:3])
        return self.mag

    def get_delta_segments(self):
        """ A delta segment must be split into lengths of self.split_size (default 1 mm) """
        if not self.needs_splitting():
            return [self]

        num_segments = np.ceil(self.get_magnitude()/self.split_size)+1
        vals = np.transpose([
                    np.linspace(
                        self.start_pos[i], 
                        self.ideal_end_pos[i], 
                        num_segments
                        ) for i in xrange(4)]) 
        vals = np.delete(vals, 0, axis=0)
        vec_segments = [dict(zip(["X", "Y", "Z", "E"], list(val))) for val in vals]
        path_segments = []

        for index, segment in enumerate(vec_segments):
            path = AbsolutePath(segment, self.speed, self.cancelable, self.use_bed_matrix, False)
            if index is not 0:
                path.set_prev(path_segments[-1])
            else:
                path.set_prev(self.prev)
            new_segments = path.get_delta_segments()

            # Stitch the new elements in
            path_segments.extend(new_segments)

        return path_segments
        

    def __str__(self):
        """ The vector representation of this path segment """
        return "Path from " + str(self.start_pos) + " to " + str(self.end_pos)

    @staticmethod
    def axis_to_index(axis):
        return Path.AXES.index(axis)

    @staticmethod
    def index_to_axis(index):
        return Path.AXES[index]

    @staticmethod
    def update_autolevel_matrix(probe_points, probe_heights):
        mat = BedCompensation.create_rotation_matrix(probe_points, probe_heights)
        Path.matrix_bed_comp = mat
        Path.matrix_bed_comp_inv = np.linalg.inv(Path.matrix_bed_comp)

class AbsolutePath(Path):
    """ A path segment with absolute movement """
    def __init__(self, axes, speed, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        Path.__init__(self, axes, speed, cancelable, use_bed_matrix, use_backlash_compensation, enable_soft_endstops)
        self.movement = Path.ABSOLUTE

    def set_prev(self, prev):
        """ Set the previous path element """
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos

        # Make the start, end and path vectors. 
        self.end_pos = np.copy(self.start_pos)
        self.ideal_end_pos = np.copy(prev.ideal_end_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.ideal_end_pos[index] = self.axes[axis]

        # Soft end stops
        if self.enable_soft_endstops:
            self.ideal_end_pos = np.clip(self.ideal_end_pos, Path.soft_min, Path.soft_max)

        self.vec = self.ideal_end_pos - self.start_pos

        # Compute stepper translation
        vec = self.transform_vector(self.vec, self.start_pos) # stepper coords
        num_steps = np.ceil(np.abs(vec) * Path.steps_pr_meter)
        self.num_steps = num_steps
        self.delta = np.sign(vec) * num_steps / Path.steps_pr_meter
        vec = self.reverse_transform_vector(self.delta, self.start_pos)

        # Calculate compensation
        self.backlash_compensate()

        # Set stepper and true posision
        self.end_pos = self.start_pos + vec
        self.stepper_end_pos = self.start_pos + self.delta
        self.rounded_vec = vec

        if np.isnan(vec).any():
            self.end_pos = self.start_pos
            self.ideal_end_pos = np.copy(prev.ideal_end_pos)
            self.num_steps = np.zeros(Path.NUM_AXES)
            self.delta = np.zeros(Path.NUM_AXES)


class RelativePath(Path):
    """ A path segment with Relative movement """
    def __init__(self, axes, speed, cancelable=False, use_bed_matrix=True, use_backlash_compensation=True, enable_soft_endstops=True):
        Path.__init__(self, axes, speed, cancelable, use_bed_matrix, use_backlash_compensation, enable_soft_endstops)
        self.movement = Path.RELATIVE

    def set_prev(self, prev):
        """ Link to previous segment """
        self.prev = prev
        prev.next = self
        self.start_pos = prev.end_pos

        # Generate the vector
        self.vec = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.vec[index] = self.axes[axis]

        self.ideal_end_pos = prev.ideal_end_pos + self.vec

        # Soft end stops
        if self.enable_soft_endstops:
            self.ideal_end_pos = np.clip(self.ideal_end_pos, Path.soft_min, Path.soft_max)

        self.vec = self.ideal_end_pos - self.start_pos

        # Compute stepper translation
        vec = self.transform_vector(self.vec, self.start_pos)
        self.num_steps = np.ceil(np.abs(vec) * Path.steps_pr_meter)
        self.delta = np.sign(vec) * self.num_steps / Path.steps_pr_meter
        vec = self.reverse_transform_vector(self.delta, self.start_pos)

        # Calculate compensation
        self.backlash_compensate()

        # Set stepper and true posision
        self.end_pos = self.start_pos + vec
        self.stepper_end_pos = self.start_pos + self.delta
        self.rounded_vec = vec

        if np.isnan(vec).any():
            self.end_pos = self.start_pos
            self.num_steps = np.zeros(Path.NUM_AXES)
            self.delta = np.zeros(Path.NUM_AXES)


class G92Path(Path):
    """ A reset axes path segment. No movement occurs, only global position
    setting """
    def __init__(self, axes, speed,  cancelable=False):
        Path.__init__(self, axes, speed)
        self.movement = Path.G92

    def set_prev(self, prev):
        """ Set the previous segment """
        self.prev = prev
        if prev is not None:
            self.start_pos = prev.end_pos
            self.ideal_end_pos = np.copy(prev.ideal_end_pos)
            prev.next = self
        else:
            self.start_pos = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)
            self.ideal_end_pos = np.copy(self.start_pos)

        self.end_pos = np.copy(self.start_pos)
        for index, axis in enumerate(Path.AXES):
            if axis in self.axes:
                self.end_pos[index] = self.ideal_end_pos[index] = self.axes[axis]
        self.vec = np.zeros(Path.NUM_AXES)
        self.rounded_vec = self.vec


class CompensationPath(Path):
    """ A path segment with relative movement and resets axes """
    def __init__(self, axes, speed, cancelable=False, use_bed_matrix=False, use_backlash_compensation=False):
        Path.__init__(self, axes, speed, cancelable, use_bed_matrix, use_backlash_compensation)
        self.movement = Path.RELATIVE

    def needs_splitting(self):
        return False

    def set_prev(self, prev):
        """ Link to previous segment """
        self.prev = prev
        prev.next = self

        # We are not moving to anywhere, really.
        self.start_pos = np.copy(prev.end_pos)
        self.ideal_end_pos = np.copy(prev.ideal_end_pos)
        self.end_pos = np.copy(prev.end_pos)

        # Set stepper and true posision
        self.stepper_end_pos = np.copy(prev.stepper_end_pos)
        self.rounded_vec = np.zeros(Path.NUM_AXES, dtype=Path.DTYPE)

        # Generate the vector 
        self.vec = self.axes

        # Compute stepper translation
        self.num_steps = np.ceil(np.abs(self.vec) * Path.steps_pr_meter)
        self.delta = np.sign(self.vec) * self.num_steps / Path.steps_pr_meter

        if np.isnan(self.vec).any():
            logging.error("Compensation Path Invalid: "+str(self.start_pos)+" to "+str(self.axes))
            self.num_steps = np.zeros(Path.NUM_AXES)
            self.delta = np.zeros(Path.NUM_AXES)

