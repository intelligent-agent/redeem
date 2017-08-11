import os
from unittest import TestCase

from redeem.Path import AbsolutePath, G92Path, Path
from redeem.Printer import Printer
import numpy as np

show_plots = True
try:
    import matplotlib.pyplot as plt
except:
    show_plots = False


def to_m(point):
    return {'X': float(point['X'])/1000, 'Y': float(point['Y'])/1000}


class ArcPathTest(TestCase):

    CW = True
    CCW = False

    def _show_plot(self, start, finish, center, paths, title):

        colors_arc = (0, 0, 0)
        color_start = (0, 1, 0)
        color_end = (1, 0, 0)
        color_center = (0, 0, 1)

        arc_x = [p.axes['X']*1000 for p in paths]
        arc_y = [p.axes['Y']*1000 for p in paths]

        # Plot
        plt.scatter(arc_x, arc_y, s=20, c=colors_arc, alpha=0.5)
        plt.scatter((start['X']*1000), (start['Y']*1000), s=300, c=color_start, alpha=0.25, marker='h')
        plt.scatter((finish['X']*1000), (finish['Y']*1000), s=100, c=color_end, alpha=0.25, marker='h')
        plt.scatter((center['X']*1000), (center['Y']*1000), s=100, c=color_center, alpha=0.25, marker='h')

        plt.title(title)
        plt.xlabel('x (mm)')
        plt.ylabel('y (mm)')

        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        plt.savefig(os.path.join('tmp', "{}.png".format(title)))
        plt.clf()

    def _test_arc(self, start, finish, center, direction, title):

        printer = Printer()

        speed = 0.001
        accel = 0.001

        prev_path = G92Path(start)
        prev_path.printer = printer
        prev_path.set_prev(None)

        path = AbsolutePath(finish, speed, accel)
        path.printer = printer
        path.set_prev(prev_path)
        path.movement = Path.G2 if direction else Path.G3

        path.I = center['X'] - start['X']
        path.J = center['Y'] - start['Y']
        radius = np.sqrt(path.I**2 + path.J**2)

        paths = path.get_segments()

        num_paths = len(paths)

        self.assertGreater(num_paths, 0)

        first = paths[0]

        self.assertEqual(first.prev.axes['X'], start['X'])
        self.assertEqual(first.prev.axes['Y'], start['Y'])

        for idx, path in enumerate(paths):

            x = path.axes['X']
            y = path.axes['Y']
            xc = center['X']
            yc = center['Y']

            circle = (x - xc)**2 + (y - yc)**2
            rsquared = radius**2
            match = np.isclose(rsquared, circle, rtol=1e-20, atol=1e-15)
            self.assertTrue(match, "{} vs. {} ({}, {}) #{}".format(rsquared, circle, path.axes, center, idx))

        if show_plots:
            self._show_plot(start, finish, center, paths, title)

    def test_very_small_arc(self):
        start = {'X': 0.0/1000, 'Y': 1.0/1000}
        finish = {'X': 1.2803/1000, 'Y': 1.5303/1000}
        center = {'X': 0.750/1000, 'Y': 1.0/1000}

        self._test_arc(start, finish, center, self.CCW, 'test_very_small_arcs')

    def test_machinenet_example_ccw(self):

        start = {'X': 0.0/100, 'Y': 1.0/100}
        finish = {'X': 1.2803/100, 'Y': 1.5303/100}
        center = {'X': 0.750/100, 'Y': 1.0/100}

        self._test_arc(start, finish, center, self.CCW, 'test_machinenet_example_ccw')

    def test_start_quadrant_3_end_quadrant_2_cw(self):

        start = {'X': -25.0, 'Y': 0.0}
        end = {'X': -8.0, 'Y': 21.464}
        center = {'X': -8.0, 'Y': 4.0}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_start_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_2_ccw(self):
        start = {'X': -25, 'Y': 0}
        end = {'X': -8, 'Y': 21.464}
        center = {'X': -8, 'Y': 4}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_start_quadrant_3_end_quadrant_2_ccw')

    def test_full_circle_ccw(self):
        start = {'Y': 10, 'X': 0}
        end = {'Y': 10, 'X': 0}
        center = {'Y': 10, 'X': 7.5}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_full_circle_ccw')

    def test_full_circle_cw(self):
        start = {'Y': 10, 'X': 0}
        end = {'Y': 10, 'X': 0}
        center = {'Y': 10, 'X': 7.5}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_full_circle_cw')

    def test_inverted_start_end_point_ccw(self):
        start = {'Y': -2, 'X': 7}
        end = {'Y': -6, 'X': -7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_inverted_start_end_point_ccw')

    def test_inverted_start_end_point_cw(self):
        start = {'Y': -2, 'X': 7}
        end = {'Y': -6, 'X': -7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_inverted_start_end_point_cw')

    def test_machinenet_example_cw(self):
        start = {'Y': 10.0, 'X': 0.0}
        end = {'Y': 15.303, 'X': 12.803}
        center = {'Y': 10.0, 'X': 7.5}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_machinenet_example_cw')

    def test_quarter_circle_quadrant_1_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': 12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_quarter_circle_quadrant_1_ccw')

    def test_quarter_circle_quadrant_1_cw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': 12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_quarter_circle_quadrant_1_cw')

    def test_start_quadrant_3_end_quadrant_1_ccw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': 11, 'X': 4.481}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_start_quadrant_3_end_quadrant_1_ccw')

    def test_start_quadrant_3_end_quadrant_1_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': 11, 'X': 4.481}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_start_quadrant_3_end_quadrant_1_cw')

    def test_quadrant_3_end_quadrant_2_ccw(self):
        start = {'Y': 0, 'X': -25}
        end = {'Y': 21.464, 'X': -8}
        center = {'Y': 4, 'X': -8}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_quadrant_3_end_quadrant_2_ccw')

    def test_quadrant_3_end_quadrant_2_cw(self):
        start = {'Y': 0, 'X': -25}
        end = {'Y': 21.464, 'X': -8}
        center = {'Y': 4, 'X': -8}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_3_ccw(self):
        start = {'Y': -12, 'X': -14}
        end = {'Y': -14.2, 'X': -8}
        center = {'Y': 6, 'X': -4}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_start_quadrant_3_end_quadrant_3_ccw')

    def test_start_quadrant_3_end_quadrant_3_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -7.1, 'X': -4}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_ccw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -2, 'X': 7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -2, 'X': 7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CW, 'test_start_quadrant_3_end_quadrant_4_cw')

    def test_three_quarter_circle_quadrant_2_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': -12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(to_m(start), to_m(end), to_m(center), self.CCW, 'test_three_quarter_circle_quadrant_2_ccw')

    # def test_pos_radius_variant_cw
    # def test_pos_radius_variant_ccw
    # def test_neg_radius_variant_cw
    # def test_neg_radius_variant_ccw
