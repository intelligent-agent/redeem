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
        plt.scatter((start['X']*1000), (start['Y']*1000), s=300, c=color_start, alpha=1, marker='h')
        plt.scatter((finish['X']*1000), (finish['Y']*1000), s=100, c=color_end, alpha=1, marker='h')
        plt.scatter((center['X']*1000), (center['Y']*1000), s=100, c=color_center, alpha=1, marker='h')

        if title:
            plt.title(title)

        plt.savefig(os.path.join("/tmp/redeem/", "{}.png".format(title)))

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
            match = np.isclose(rsquared, circle, rtol=1e-20, atol=1e-15 )
            self.assertTrue(match, "{} vs. {} ({}, {}) #{}".format(rsquared, circle, path.axes, center, idx))

        if show_plots:
            self._show_plot(start, finish, center, paths, title)


    def test_machinenet_example(self):

        start = {'X': 0.0/1000, 'Y': 1.0/1000}
        finish = {'X': 1.2803/1000, 'Y': 1.5303/1000}
        center = {'X': 0.750/1000, 'Y': 1.0/1000}

        self._test_arc(start, finish, center, self.CW, 'machinenet_example')

    def test_start_quadrant_3_end_quadrant_2_cw(self):

        start = {'X': -25.0/1000, 'Y': 0.0/1000}
        finish = {'X': -8.0/1000, 'Y': 21.464/1000}
        center = {'X': -8.0/1000, 'Y': 4.0/1000}

        self._test_arc(start, finish, center, self.CW, 'test_start_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_2_ccw(self):
        start = {'X': -25.0/1000, 'Y': 0}
        finish = {'X': -8.0/1000, 'Y': 21.464/1000}
        center = {'X': -8.0/1000, 'Y': 4.0/1000}

        self._test_arc(start, finish, center, self.CCW, 'test_start_quadrant_3_end_quadrant_2_ccw')

        #     x0 = -25
        #     y0 = 0
        #
        #     x1 = -8
        #     y1 = 21.464
        #
        #     i = 17
        #     j = 4





    # def test_(self):
    #
    #     start = {'X': 0/1000, 'Y': 0/1000}
    #     finish = {'X': 0/1000, 'Y': 0/1000}
    #     center = {'X': 0/1000, 'Y': 0/1000}
    # def test_(self):
    #
    #     start = {'X': 0/1000, 'Y': 0/1000}
    #     finish = {'X': 0/1000, 'Y': 0/1000}
    #     center = {'X': 0/1000, 'Y': 0/1000}
    # def test_(self):
    #
    #     start = {'X': 0/1000, 'Y': 0/1000}
    #     finish = {'X': 0/1000, 'Y': 0/1000}
    #     center = {'X': 0/1000, 'Y': 0/1000}
    # def test_(self):
    #
    #     start = {'X': 0/1000, 'Y': 0/1000}
    #     finish = {'X': 0/1000, 'Y': 0/1000}
    #     center = {'X': 0/1000, 'Y': 0/1000}

