"""
Delta printer linear least squares autocalibration.

Most of the code in this package is a pretty straightforward
translation of David Crocker's linear least squares calibration
algorithm: http://escher3d.com/pages/wizards/wizarddelta.php .

For additional information on the algorithm, visit the following
Wikipedia page:
https://en.wikipedia.org/wiki/Linear_least_squares_(mathematics)

Author: Matti Airas
email: mairas(at)iki(dot)fi
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

import copy
import logging

import numpy as np
from scipy.optimize import leastsq as least_squares

def calculate_probe_points(max_radius, radius_steps=2, angle_steps=6):
    """
    Calculate a set of probe points for delta printer calibration.
    :param max_radius: Maximum radius of the outmost probe circle
    :param radius_steps: Probe points along each radial circle
    :param angle_steps: Number of radial circles to probe
    :return: An iterator yielding x, y tuples (in mm units)
    """
    radius_increment = max_radius / radius_steps
    angle_increment = 360. / angle_steps
    first = True
    for i in range(radius_steps + 1):
        r = i * radius_increment
        for j in range(angle_steps):
            alpha = j * angle_increment
            x = r * np.cos(np.radians(alpha))
            y = r * np.sin(np.radians(alpha))
            if i > 0 or first:
                yield x, y
                first = False


def get_g29_macro(max_radius, radius_steps, angle_steps, z=5.):
    lines = []
    xys = list(calculate_probe_points(max_radius, radius_steps, angle_steps))
    for i, (x, y) in enumerate(xys):
        lines.append("M557 P{} X{} Y{} Z{}".format(i, x, y, z))
    lines.append("G32")
    lines.append("G28")
    for i in range(len(xys)):
        lines.append("G30 P{} S".format(i))
    lines.append("G31")
    lines.append("G1 X0.0 Y0.0")
    return "\n".join(lines)


# enums
A_AXIS, B_AXIS, C_AXIS = 0, 1, 2


# this class somewhat duplicates the Delta class of the native path planner
# but as it is, the Delta class interface doesn't amend itself easily to
# the purposes of the auto calibration calculation.

class AutoCalibrationDeltaParameters:
    def __init__(self, diagonal, radius, height,
                 xstop, ystop, zstop,
                 yadj, zadj):
        self.diagonal = diagonal
        self.radius = radius
        self.height = height
        self.xstop = xstop
        self.ystop = ystop
        self.zstop = zstop
        self.yadj = yadj
        self.zadj = zadj

        # internal parameters

        self.towerX = None
        self.towerY = None
        self.Xbc = None
        self.Xca = None
        self.Xab = None
        self.Ybc = None
        self.Yca = None
        self.Yab = None
        self.coreFa = None
        self.coreFb = None
        self.coreFc = None
        self.Q = None
        self.Q2 = None
        self.D2 = None

        self.recalculate()

    @classmethod
    def from_redeem_delta(cls, delta, center_offsets):
        if delta.Ae != delta.Be or delta.Ae != delta.Ce:
            raise ValueError("non-uniform effector offsets not supported")

        diagonal = 1000. * delta.L
        radius = 1000. * (delta.r - delta.Ae)

        # center_offsets are negative, hence the minus sign
        xstop = -1000. * center_offsets["X"]
        ystop = -1000. * center_offsets["Y"]
        zstop = -1000. * center_offsets["Z"]

        height = min(xstop, ystop, zstop)

        xstop -= height
        ystop -= height
        zstop -= height

        yadj = 1000. * (delta.B_tangential - delta.A_tangential)
        zadj = 1000. * (delta.C_tangential - delta.A_tangential)

        logging.debug("input delta parameters: Diagonal (L) = %f", diagonal/1000.)
        logging.debug("input delta parameters: Radius   (r) = %f", radius/1000.)
        logging.debug("input delta parameters: offset_x     = %f", center_offsets["X"])
        logging.debug("input delta parameters: offset_y     = %f", center_offsets["Y"])
        logging.debug("input delta parameters: offset_z     = %f", center_offsets["Z"])
        logging.debug("input delta parameters: A_tangential = %f", delta.A_tangential)
        logging.debug("input delta parameters: B_tangential = %f", delta.B_tangential)
        logging.debug("input delta parameters: C_tangential = %f", delta.C_tangential)
        logging.debug("input delta parameters: yadj         = %f", yadj/1000.)
        logging.debug("input delta parameters: zadj         = %f", zadj/1000.)

        return cls(diagonal, radius, height,
                   xstop, ystop, zstop,
                   yadj, zadj)

    def to_redeem_delta(self, delta, center_offsets):
        delta.Hez = 0.
        delta.L = self.diagonal / 1000.
        delta.r = self.radius / 1000.
        delta.Ae = 0.
        delta.Be = 0.
        delta.Ce = 0.
        delta.A_radial = 0.
        delta.B_radial = 0.
        delta.C_radial = 0.
        delta.A_tangential = 0
        delta.B_tangential = self.yadj / 1000.
        delta.C_tangential = self.zadj / 1000.

        center_offsets["X"] = -1. * (self.height + self.xstop) / 1000.
        center_offsets["Y"] = -1. * (self.height + self.ystop) / 1000.
        center_offsets["Z"] = -1. * (self.height + self.zstop) / 1000.

        logging.debug("output delta parameters: Diagonal (L) = %f", delta.L)
        logging.debug("output delta parameters: Radius   (r) = %f", delta.r)
        logging.debug("output delta parameters: offset_x     = %f", center_offsets['X'])
        logging.debug("output delta parameters: offset_y     = %f", center_offsets['Y'])
        logging.debug("output delta parameters: offset_z     = %f", center_offsets['Z'])
        logging.debug("output delta parameters: A_tangential = %f", delta.A_tangential)
        logging.debug("output delta parameters: B_tangential = %f", delta.B_tangential)
        logging.debug("output delta parameters: C_tangential = %f", delta.C_tangential)
        logging.debug("output delta parameters: yadj         = %f", self.yadj)
        logging.debug("output delta parameters: zadj         = %f", self.zadj)

    @classmethod
    def from_base_and_raw_params(cls, base, new_params):
        ret = None

        if len(new_params) == 3:
            ret = cls(base.diagonal, base.radius, base.height, new_params[0], new_params[1], new_params[2], base.yadj, base.zadj)
        elif len(new_params) == 4:
            ret = cls(base.diagonal, new_params[0], base.height, new_params[1], new_params[2], new_params[3], base.yadj, base.zadj)
        elif len(new_params) == 6:
            ret = cls(base.diagonal, new_params[0], base.height, new_params[1], new_params[2], new_params[3], new_params[4], new_params[5])
        elif len(new_params) == 7:
            ret = cls(new_params[0], new_params[1], base.height, new_params[2], new_params[3], new_params[4], new_params[5], new_params[6])
        else:
            raise ValueError("Only 3, 4, 6, or 7 parameters supported")

        ret.update_height(base)
        return ret

    def to_raw_params(self, num_factors):
        if num_factors == 3:
            return [self.xstop, self.ystop, self.zstop]
        elif num_factors == 4:
            return [self.radius, self.xstop, self.ystop, self.zstop]
        elif num_factors == 6:
            return [self.radius, self.xstop, self.ystop, self.zstop, self.yadj, self.zadj]
        elif num_factors == 7:
            return [self.diagonal, self.radius, self.xstop, self.ystop, self.zstop, self.yadj, self.zadj]

    def to_dict(self):
        L = self.diagonal / 1000.
        r = self.radius / 1000.
        A_tangential = 0
        B_tangential = self.yadj / 1000.
        C_tangential = self.zadj / 1000.

        offset_x = -1. * (self.height + self.xstop) / 1000.
        offset_y = -1. * (self.height + self.ystop) / 1000.
        offset_z = -1. * (self.height + self.zstop) / 1000.

        out = {}
        out["L"] = L
        out["r"] = r
        out["A_tangential"] = A_tangential
        out["B_tangential"] = B_tangential
        out["C_tangential"] = C_tangential
        out["offset_x"] = offset_x
        out["offset_y"] = offset_y
        out["offset_z"] = offset_z

        return out

    def recalculate(self):
        self.towerX = []
        self.towerY = []
        self.towerX.append(self.radius * np.cos(np.radians(90.)))
        self.towerY.append(self.radius * np.sin(np.radians(90.)))
        self.towerX.append(self.radius * np.cos(np.radians(210. + self.yadj)))
        self.towerY.append(self.radius * np.sin(np.radians(210. + self.yadj)))
        self.towerX.append(self.radius * np.cos(np.radians(330. + self.zadj)))
        self.towerY.append(self.radius * np.sin(np.radians(330. + self.zadj)))

        self.Xbc = self.towerX[2] - self.towerX[1]
        self.Xca = self.towerX[0] - self.towerX[2]
        self.Xab = self.towerX[1] - self.towerX[0]
        self.Ybc = self.towerY[2] - self.towerY[1]
        self.Yca = self.towerY[0] - self.towerY[2]
        self.Yab = self.towerY[1] - self.towerY[0]
        self.coreFa = self.towerX[0]**2 + self.towerY[0]**2
        self.coreFb = self.towerX[1]**2 + self.towerY[1]**2
        self.coreFc = self.towerX[2]**2 + self.towerY[2]**2
        self.Q = 2 * (self.Xca * self.Yab - self.Xab * self.Yca)
        self.Q2 = self.Q**2
        self.D2 = self.diagonal**2

    def update_height(self, base):
        old_point = base.inverse_transform(0, 0, 0, True)
        new_point = self.inverse_transform(0, 0, 0, True)
        height_change = new_point[2] - old_point[2]
        self.height += height_change

    def transform(self, pos, ignore_endstops = False):
        x, y, z = pos
        Ha = z + np.sqrt(self.D2 -
                           (x - self.towerX[0])**2 -
                           (y - self.towerY[0])**2)
        Hb = z + np.sqrt(self.D2 -
                           (x - self.towerX[1])**2 -
                           (y - self.towerY[1])**2)
        Hc = z + np.sqrt(self.D2 -
                           (x - self.towerX[2])**2 -
                           (y - self.towerY[2])**2)
        if ignore_endstops:
            return [Ha, Hb, Hc]
        else:
            return [Ha - self.xstop, Hb - self.ystop, Hc - self.zstop]

    def inverse_transform(self, a, b, c, ignore_endstops = False):
        Ha = a
        Hb = b
        Hc = c
        if not ignore_endstops:
            Ha += self.xstop
            Hb += self.ystop
            Hc += self.zstop

        Fa = self.coreFa + Ha**2
        Fb = self.coreFb + Hb**2
        Fc = self.coreFc + Hc**2

        # Setup PQRSU such that x = -(S - uz)/P, y = (P - Rz)/Q
        P = self.Xbc*Fa + self.Xca*Fb + self.Xab*Fc
        S = self.Ybc*Fa + self.Yca*Fb + self.Yab*Fc
        R = 2 * (self.Xbc*Ha + self.Xca*Hb + self.Xab*Hc)
        U = 2 * (self.Ybc*Ha + self.Yca*Hb + self.Yab*Hc)

        R2 = R**2
        U2 = U**2

        A = U2 + R2 + self.Q2
        minusHalfB = (S*U + P*R + Ha*self.Q2 +
                      self.towerX[A_AXIS]*U*self.Q -
                      self.towerY[A_AXIS]*R*self.Q)
        C = ((S + self.towerX[A_AXIS]*self.Q)**2 +
             (P - self.towerY[A_AXIS]*self.Q)**2 +
             (Ha**2 - self.D2)*self.Q2)

        z = (minusHalfB - np.sqrt(minusHalfB**2 - A*C)) / A
        x = (U*z - S) / self.Q
        y = (P - R*z) / self.Q

        return x, y, z


def _expected_residuals(new_raw_delta_params, points, base_delta_params, probe_motor_positions):
    new_delta_params = AutoCalibrationDeltaParameters.from_base_and_raw_params(base_delta_params, new_raw_delta_params)
    new_points = map(lambda motor_position: new_delta_params.inverse_transform(motor_position[0], motor_position[1], motor_position[2]), probe_motor_positions)
    new_residuals = []
    for i in range(0, len(new_points)):
        error = points[2][i] - new_points[i][2]
        new_residuals.append(error)
    return new_residuals

def _calibrate_delta_parameters(pts, num_factors, delta_params):
    num_points = len(pts[0])

    # validate the input

    if num_factors < 3 or num_factors > 7 or num_factors == 5:
        raise ValueError("{} factors requested but only 3, 4, 6, 7 supported"
                         .format(num_factors))
    if num_factors > num_points:
        raise ValueError("Need at least as many points as factors")

    # Transform the probing points to motor endpoints and store them
    # in a matrix, so that we can do multiple iterations using the same data

    probe_motor_positions = np.zeros((num_points, 3))
    corrections = np.zeros(num_points)

    for i, (x, y, z) in enumerate(zip(*pts)):
        probe_motor_positions[i, :] = delta_params.transform([x, y, 0.0])

    initial_sum_of_squares = np.sum(pts[2] ** 2)

    print("initial deviation: {}".format(initial_sum_of_squares))

    raw_params = delta_params.to_raw_params(num_factors)

    new_raw_params = least_squares(_expected_residuals, raw_params, args=(pts, delta_params, probe_motor_positions))[0]

    return AutoCalibrationDeltaParameters.from_base_and_raw_params(delta_params, new_raw_params)

def delta_auto_calibration(delta, center_offsets,
                           num_factors,
                           simulate_only,
                           probe_points, print_head_zs):

    # convert the Delta class representation to AutoCalibrationDeltaParameters

    delta_params = AutoCalibrationDeltaParameters.from_redeem_delta(
        delta, center_offsets)

    # adjust the coordinate representation

    xs = []
    ys = []
    zs = []

    for i in range(len(probe_points)):
        xs.append(probe_points[i]["X"])
        ys.append(probe_points[i]["Y"])
        zs.append(print_head_zs[i])

    xs = np.array(xs)
    ys = np.array(ys)
    zs = np.array(zs) * -1

    pts = xs, ys, zs

    logging.debug("points for calibration: " + str(pts))

    # do the calibration

    new_delta_params = _calibrate_delta_parameters(
            pts, num_factors, delta_params)

    # if not just simulating, adjust the bot parameters

    if not simulate_only:
        new_delta_params.to_redeem_delta(delta, center_offsets)

    return new_delta_params.to_dict()

if __name__ == '__main__':
    real_printer_params = AutoCalibrationDeltaParameters(304.188, 160, 265, 0, 0, 0, 0, 0)
    fake_printer_params = real_printer_params

    angles = np.radians([90.0, 150.0, 210.0, 270.0, 330.0, 30.0])
    radii = [25, 50, 75]
    points = []
    for radius in radii:
        for angle in angles:
            points.append([radius * np.cos(angle), radius * np.sin(angle)])

    xs = [0., 0., -43.3, -43.3, 0., 43.3, 43.3, 0., -64.95, -64.95, 0., 64.95]
    ys = [0., 50., 25., -25., -50., -25., 25., 75., 37.5, -37.5, -75., -37.5]
#    zs = [-1.1, -2.75, -1.78, -1.23, -1.6, -2.49, -3.13, -4.34, -2.96, -2.1, -2.65, -3.92, -6.85]
    zs = [-10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10., -10. ]
#    xs = []
#    ys = []
#    zs = []
#    for point in points:
#        stripped_point = [point[0], point[1], 0]
#        delta_point = fake_printer_params.transform(stripped_point)
#        real_point = real_printer_params.inverse_transform(delta_point[0], delta_point[1], delta_point[2])
#        xs.append(point[0])
#        ys.append(point[1])
#        zs.append(real_point[2])

    calculated_printer_params = _calibrate_delta_parameters((np.array(xs), np.array(ys), np.array(zs) * -1), 3, fake_printer_params)

    print("real: " + str(real_printer_params.to_dict()))
    print("calculated: " + str(calculated_printer_params.to_dict()))
    print(str([real_printer_params.xstop, real_printer_params.ystop, real_printer_params.zstop]))
    print(str([calculated_printer_params.xstop, calculated_printer_params.ystop, calculated_printer_params.zstop]))
