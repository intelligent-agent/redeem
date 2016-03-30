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
                 xadj, yadj, zadj):
        self.diagonal = diagonal
        self.radius = radius
        self.height = height
        self.xstop = xstop
        self.ystop = ystop
        self.zstop = zstop
        self.xadj = xadj
        self.yadj = yadj
        self.zadj = zadj

        self.homed_carriage_height = None

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
        cox = -1000. * center_offsets["X"]
        coy = -1000. * center_offsets["Y"]
        coz = -1000. * center_offsets["Z"]

        height = np.mean([cox, coy, coz]) - delta.Hez
        xstop = cox - height
        ystop = coy - height
        zstop = coz - height
        xadj = delta.A_tangential
        yadj = delta.B_tangential
        zadj = delta.C_tangential

        logging.debug("input delta parameters: diagonal = %f", diagonal)
        logging.debug("input delta parameters: radius = %f", radius)
        logging.debug("input delta parameters: height = %f", height)
        logging.debug("input delta parameters: xstop = %f", xstop)
        logging.debug("input delta parameters: ystop = %f", ystop)
        logging.debug("input delta parameters: zstop = %f", zstop)
        logging.debug("input delta parameters: xadj = %f", xadj)
        logging.debug("input delta parameters: yadj = %f", yadj)
        logging.debug("input delta parameters: zadj = %f", zadj)

        return cls(diagonal, radius,
                   height,
                   xstop, ystop, zstop,
                   xadj, yadj, zadj)

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
        delta.A_tangential = self.xadj
        delta.B_tangential = self.yadj
        delta.C_tangential = self.zadj

        cox = self.height + self.xstop
        coy = self.height + self.ystop
        coz = self.height + self.zstop

        center_offsets["X"] = -1. * cox / 1000.
        center_offsets["Y"] = -1. * coy / 1000.
        center_offsets["Z"] = -1. * coz / 1000.

        logging.debug("output delta parameters: L = %f", delta.L)
        logging.debug("output delta parameters: r = %f", delta.r)
        logging.debug("output delta parameters: A_tangential = %f",
                      delta.A_tangential)
        logging.debug("output delta parameters: B_tangential = %f",
                      delta.B_tangential)
        logging.debug("output delta parameters: C_tangential = %f",
                      delta.C_tangential)
        logging.debug("output delta parameters: center_offsets['X'] = %f",
                      center_offsets['X'])
        logging.debug("output delta parameters: center_offsets['Y'] = %f",
                      center_offsets['Y'])
        logging.debug("output delta parameters: center_offsets['Z'] = %f",
                      center_offsets['Z'])

    def recalculate(self):
        self.towerX = []
        self.towerY = []
        self.towerX.append(self.radius * np.cos(np.radians(90. + self.xadj)))
        self.towerY.append(self.radius * np.sin(np.radians(90. + self.xadj)))
        self.towerX.append(self.radius * np.cos(np.radians(210. + self.yadj)))
        self.towerY.append(self.radius * np.sin(np.radians(210. + self.yadj)))
        self.towerX.append(self.radius * np.cos(np.radians(310. + self.zadj)))
        self.towerY.append(self.radius * np.sin(np.radians(310. + self.zadj)))

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

        # Calculate the base carriage height when the printer is homed.
        temp_height = self.diagonal  # any sensible height will do here
        _, _, _z_temp = self.inverse_transform(
                temp_height, temp_height, temp_height)
        self.homed_carriage_height = (
            self.height + temp_height - _z_temp)

    def transform(self, pos, axis):
        x, y, z = pos
        return z + np.sqrt(self.D2 -
                           (x - self.towerX[axis])**2 -
                           (y - self.towerY[axis])**2)

    def transform_all(self, pos):
        return [self.transform(pos, ax) for ax in range(3)]

    def inverse_transform(self, Ha, Hb, Hc):
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

    def compute_derivative(self, deriv, ha, hb, hc, perturb=0.2):
        hi_params = copy.deepcopy(self)
        lo_params = copy.deepcopy(self)

        ha_hi = ha_lo = ha
        hb_hi = hb_lo = hb
        hc_hi = hc_lo = hc

        if deriv == 0:
            ha_hi = ha + perturb
            ha_lo = ha - perturb
        elif deriv == 1:
            hb_hi = hb + perturb
            hb_lo = hb - perturb
        elif deriv == 2:
            hc_hi = hc + perturb
            hc_lo = hc - perturb
        elif deriv == 3:
            hi_params.radius += perturb
            lo_params.radius -= perturb
        elif deriv == 4:
            hi_params.xadj += perturb
            lo_params.xadj -= perturb
        elif deriv == 5:
            hi_params.yadj += perturb
            lo_params.yadj -= perturb
        elif deriv == 6:
            hi_params.diagonal += perturb
            lo_params.diagonal -= perturb
        else:
            raise ValueError("invalid derivative index")

        hi_params.recalculate()
        lo_params.recalculate()

        _, _, z_hi = hi_params.inverse_transform(ha_hi, hb_hi, hc_hi)
        _, _, z_lo = lo_params.inverse_transform(ha_lo, hb_lo, hc_lo)

        return (z_hi - z_lo) / (2 * perturb)

    def build_derivative_matrix(self,
                                num_points,
                                num_factors,
                                probe_motor_positions):
        # Build a Nx7 matrix of derivatives with respect to
        # xa, xb, yc, za, zb, zc, diagonal.
        derivative_matrix = np.zeros((num_points, num_factors))
        for i in range(num_points):
            for j in range(num_factors):
                derivative_matrix[i, j] = self.compute_derivative(
                        j, *probe_motor_positions[i, :])
        return derivative_matrix

    def adjust(self, num_factors, v):
        old_carriage_height_A = self.homed_carriage_height + self.xstop

        # Update endstop adjustments
        self.xstop += v[0]
        self.ystop += v[1]
        self.zstop += v[2]

        if num_factors >= 4:
            self.radius += v[3]

            if num_factors >= 6:
                self.xadj += v[4]
                self.yadj += v[5]

                if num_factors == 7:
                    self.diagonal += v[6]

            self.recalculate()

        # Adjusting the diagonal and the tower positions affects the
        # homed carriage height. We need to adjust homedHeight to allow for
        # this, to get the change that was requested in the endstop corrections.

        height_error = (self.homed_carriage_height +
                        self.xstop -
                        old_carriage_height_A -
                        v[0])
        self.height -= height_error
        self.homed_carriage_height -= height_error


def _calibrate_delta_parameters(pts, num_factors, delta_params):
    xs, ys, zs = pts
    num_points = len(zs)

    # validate the input

    if num_factors < 3 or num_factors > 7:
        raise ValueError("{} factors requested but only 3-7 supported"
                         .format(num_factors))
    if num_factors > num_points:
        raise ValueError("Need at least as many points as factors")

    # Transform the probing points to motor endpoints and store them
    # in a matrix, so that we can do multiple iterations using the same data

    probe_motor_positions = np.zeros((num_points, 3))
    corrections = np.zeros(num_points)

    for i, (x, y, z) in enumerate(zip(*pts)):
        probe_motor_positions[i, :] = delta_params.transform_all([x, y, 0.0])

    initial_sum_of_squares = np.sum(pts[2] ** 2)

    print("initial deviation: {}".format(initial_sum_of_squares))

    # Do 1 or more Newton-Raphson iterations

    iteration = 0
    expected_residuals = []

    while True:
        derivative_matrix = delta_params.build_derivative_matrix(
                num_points, num_factors, probe_motor_positions)

        # Now build the matrices for linear least squares fitting

        gramian_matrix = np.dot(derivative_matrix.T, derivative_matrix)
        xty = np.dot(derivative_matrix.T, -zs + corrections)
        beta = np.dot(np.linalg.inv(gramian_matrix), xty)

        delta_params.adjust(num_factors, beta)

        probe_motor_positions = probe_motor_positions

        # Calculate the expected probe heights using the new parameters
        expected_residuals = np.zeros(num_points)
        for i in range(num_points):
            probe_motor_positions[i, :] += beta[0:3]
            _, _, new_Z = delta_params.inverse_transform(
                    *probe_motor_positions[i, :])
            corrections[i] = -new_Z
            expected_residuals[i] = zs[i] + new_Z

        sum_of_squares = np.sum(expected_residuals ** 2)

        expected_rms_error = np.sqrt(sum_of_squares/num_points)

        print("expected deviation after iteration {}: {}".format(
                iteration, expected_rms_error))

        iteration += 1

        # parameters will converge in two iterations
        if iteration == 2:
            break

    return expected_residuals


def _filter_outliers(pts, expected_residuals, max_std):

    res_std = np.std(expected_residuals)
    k = max_std * res_std

    xs, ys, zs = pts
    m = np.mean(expected_residuals)
    pts2 = tuple(zip(*[(x, y, z) for x, y, z, r
                       in zip(xs, ys, zs, expected_residuals)
                       if np.abs(r-m) < k]))
    pts2 = [np.array(x) for x in pts2]
    return pts2


def delta_auto_calibration(delta, center_offsets,
                           num_factors, max_std,
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
    zs = np.array(zs)

    pts = xs, ys, zs

    # do the calibration

    expected_residuals = _calibrate_delta_parameters(
            pts, num_factors, delta_params)

    res_mean = np.mean(expected_residuals)

    # if max_std is set, remove outliers and do the second round

    if max_std is not None:

        # remove outliers
        pts_f = _filter_outliers(pts, expected_residuals, max_std)
        logging.info("delta_auto_calibration: removed %d outliers",
                     len(pts[0])-len(pts_f[0]))

        # re-do the calibration

        expected_residuals_f = _calibrate_delta_parameters(
                pts, num_factors, delta_params)

        res_mean_f = np.mean(expected_residuals_f)

        logging.info("delta_auto_calibration: outlier removal improved "
                     "mean residuals by %f", res_mean - res_mean_f)

    # if not just simulating, adjust the bot parameters

    if not simulate_only:
        delta_params.to_redeem_delta(delta, center_offsets)
