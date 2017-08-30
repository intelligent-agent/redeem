import os
import logging
import numpy as np
from mock import Mock

from MockPrinter import MockPrinter

show_plots = False
try:
    import pygal
except:
    show_plots = False

base_dir = os.path.dirname(os.path.dirname(__file__))


class G2_G3_Tests(MockPrinter):

    CW = 1
    CCW = 2

    @classmethod
    def setUpPatch(cls):
        cls.printer.path_planner.native_planner = Mock()
        cls.printer.ensure_steppers_enabled = Mock()

    def setUp(self):
        self.printer.unit_factor = self.f = 1

    def _show_plot(self, start, finish, center, points, title):

        from pygal.style import Style

        custom_style = Style(
            colors=('#aaaaaa', '#00ff00', '#ff0000', '#0000ff')
        )

        xy_chart = pygal.XY(stroke=False, style=custom_style)
        xy_chart.title = title
        xy_chart.add('path', points)
        xy_chart.add('start', [(start['X'], start['Y'])])
        xy_chart.add('finish', [(finish['X'], finish['Y'])])
        xy_chart.add('center', [(center['X'], center['Y'])])
        xy_chart.render_to_file('{}.svg'.format(title))

    def _build_start_code(self, start):
        gcode = 'G1'
        for axis, val in start.items():
            gcode += ' {}{}'.format(axis, val)
        return gcode

    def _build_curve_code(self, finish, offset, direction):
        gcode = 'G{}'.format(2 if direction is self.CW else 3)
        for axis, val in finish.items():
            gcode += ' {}{}'.format(axis, val)

        for axis, val in offset.items():
            if val:
                gcode += ' {}{}'.format(axis, val)

        return gcode

    def assertCloseTo(self, a, b, msg=''):
        match = np.isclose(a, b, rtol=1e-6, atol=1e-6)
        if not match:
            exception = self._formatMessage(msg, "{} is not close to {}: {}".format(a, b, msg))
            raise self.failureException(exception)

    def _test_arc(self, start, finish, center, direction, title):

        offset = {'I': center['X'] - start['X'], 'J': center['Y'] - start['Y']}

        gcodes = [
            'G17',
            self._build_start_code(start),
            self._build_curve_code(finish, offset, direction)
        ]

        logging.debug("gcodes: {}".format(gcodes))

        for gcode in gcodes:
            self.execute_gcode(gcode)

        queue_mock = self.printer.path_planner.native_planner.queueMove

        queued_points = [args[0][0] for args in queue_mock.call_args_list]

        for point in queued_points:
            print(point)
            logging.debug("queued point: {}".format(point))

        # pop the G1 positioning command (start point)
        initial = queued_points.pop(0)

        points = [(point[0]*1000, (point[1]*1000)) for point in queued_points]

        if show_plots:
            self._show_plot(start, finish, center, points, title)

        logging.debug("initial: {}".format(initial))
        logging.debug("start: {}".format(start))

        self.assertCloseTo(initial[0], start['X']/1000)
        self.assertCloseTo(initial[1], start['Y']/1000)

        radius = np.sqrt((offset['I']/1000)**2 + (offset['J']/1000)**2)

        for idx, point in enumerate(queued_points):

            x = point[0]
            y = point[1]
            xc = center['X']/1000
            yc = center['Y']/1000

            circle = (x - xc)**2 + (y - yc)**2
            rsquared = radius**2
            self.assertCloseTo(rsquared, circle)

        final = queued_points[-1]
        self.assertCloseTo(final[0], finish['X']/1000)
        self.assertCloseTo(final[1], finish['Y']/1000)

        queue_mock.reset_mock()

    def test_very_small_arc(self):
        start = {'X': 0.0, 'Y': 1.0}
        finish = {'X': 1.2803, 'Y': 1.5303}
        center = {'X': 0.750, 'Y': 1.0}

        self._test_arc(start, finish, center, self.CCW, 'test_very_small_arcs')

    def test_machinenet_example_ccw(self):
        start = {'X': 0.0, 'Y': 10.0}
        finish = {'X': 12.803, 'Y': 15.303}
        center = {'X': 7.50, 'Y': 10.0}

        self._test_arc(start, finish, center, self.CCW, 'test_machinenet_example_ccw')

    def test_start_quadrant_3_end_quadrant_2_cw(self):
        start = {'X': -25.0, 'Y': 0.0}
        end = {'X': -8.0, 'Y': 21.464}
        center = {'X': -8.0, 'Y': 4.0}

        self._test_arc(start, end, center, self.CW, 'test_start_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_2_ccw(self):
        start = {'X': -25.0, 'Y': 0.0}
        end = {'X': -8.0, 'Y': 21.464}
        center = {'X': -8.0, 'Y': 4.0}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_2_ccw')

    def test_full_circle_ccw(self):
        start = {'Y': 10.0, 'X': 0.0}
        end = {'Y': 10.0, 'X': 0.0}
        center = {'Y': 10.0, 'X': 7.5}

        self._test_arc(start, end, center, self.CCW, 'test_full_circle_ccw')

    def test_full_circle_cw(self):
        start = {'Y': 10.0, 'X': 0.0}
        end = {'Y': 10.0, 'X': 0.0}
        center = {'Y': 10.0, 'X': 7.5}

        self._test_arc(start, end, center, self.CW, 'test_full_circle_cw')

    def test_inverted_start_end_point_ccw(self):
        start = {'Y': -2.0, 'X': 7.0}
        end = {'Y': -6.0, 'X': -7.0}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CCW, 'test_inverted_start_end_point_ccw')

    def test_inverted_start_end_point_cw(self):
        start = {'Y': -2.0, 'X': 7.0}
        end = {'Y': -6.0, 'X': -7.0}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CW, 'test_inverted_start_end_point_cw')

    def test_machinenet_example_cw(self):
        start = {'Y': 10.0, 'X': 0.0}
        end = {'Y': 15.303, 'X': 12.803}
        center = {'Y': 10.0, 'X': 7.5}

        self._test_arc(start, end, center, self.CW, 'test_machinenet_example_cw')

    def test_quarter_circle_quadrant_1_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0.0, 'X': 12.0}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CCW, 'test_quarter_circle_quadrant_1_ccw')

    def test_quarter_circle_quadrant_1_cw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0.0, 'X': 12.0}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CW, 'test_quarter_circle_quadrant_1_cw')

    def test_start_quadrant_3_end_quadrant_1_ccw(self):
        start = {'Y': -6.0, 'X': -7.0}
        end = {'Y': 11.0, 'X': 4.481}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_1_ccw')

    def test_start_quadrant_3_end_quadrant_1_cw(self):
        start = {'Y': -6.0, 'X': -7.0}
        end = {'Y': 11.0, 'X': 4.481}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CW, 'test_start_quadrant_3_end_quadrant_1_cw')

    def test_quadrant_3_end_quadrant_2_ccw(self):
        start = {'Y': 0, 'X': -25.0}
        end = {'Y': 21.464, 'X': -8.0}
        center = {'Y': 4.0, 'X': -8.0}

        self._test_arc(start, end, center, self.CCW, 'test_quadrant_3_end_quadrant_2_ccw')

    def test_quadrant_3_end_quadrant_2_cw(self):
        start = {'Y': 0.0, 'X': -25.0}
        end = {'Y': 21.464, 'X': -8.0}
        center = {'Y': 4.0, 'X': -8.0}

        self._test_arc(start, end, center, self.CW, 'test_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_3_ccw(self):
        start = {'Y': -12.0, 'X': -14.0}
        end = {'Y': -14.2, 'X': -8.0}
        center = {'Y': 6.0, 'X': -4.0}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_3_ccw')

    def test_start_quadrant_3_end_quadrant_3_cw(self):
        start = {'Y': -6.0, 'X': -7.0}
        end = {'Y': -7.1, 'X': -4.0}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_ccw(self):
        start = {'Y': -6.0, 'X': -7.0}
        end = {'Y': -2.0, 'X': 7.0}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_cw(self):
        start = {'Y': -6.0, 'X': -7.0}
        end = {'Y': -2.0, 'X': 7.0}
        center = {'Y': 3.0, 'X': -2.0}

        self._test_arc(start, end, center, self.CW, 'test_start_quadrant_3_end_quadrant_4_cw')

    def test_three_quarter_circle_quadrant_2_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0.0, 'X': -12.0}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CCW, 'test_three_quarter_circle_quadrant_2_ccw')
    # def test_pos_radius_variant_cw
    # def test_pos_radius_variant_ccw
    # def test_neg_radius_variant_cw
    # def test_neg_radius_variant_ccw