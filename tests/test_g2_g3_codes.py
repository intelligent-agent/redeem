import os
from unittest import TestCase
import numpy as np

from redeem.Gcode import Gcode
from redeem.Redeem import Redeem

from mock import patch, Mock

show_plots = True
try:
    import pygal
except:
    show_plots = False

base_dir = os.path.dirname(os.path.dirname(__file__))

class G2G3CodesTest(TestCase):

    CW = 1
    CCW = 2

    def setUp(self):
        self.patcher = patch('redeem.path_planner.PathPlannerNative.PathPlannerNative')
        self.queue_mock = self.patcher.start()

        self.redeem = Redeem(os.path.join(base_dir, 'configs'))
        self.redeem.printer.enable.set_enabled()
        self.gcode_processor = self.redeem.printer.processor

        # the native planner handles processing the paths
        # create mock so that replicape doesn't send the paths to any connected stepper motors
        self.redeem.printer.path_planner.native_planner = Mock()

    def tearDown(self):
        self.redeem.exit()

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
            if val:
                gcode += ' {}{}'.format(axis, val)
        return gcode

    def _build_curve_code(self, finish, offset, direction):
        gcode = 'G{}'.format(2 if direction is self.CW else 3)
        for axis, val in finish.items():
            if val:
                gcode += ' {}{}'.format(axis, val)

        for axis, val in offset.items():
            if val:
                gcode += ' {}{}'.format(axis, val)

        return gcode

    def assertCloseTo(self, a, b, msg=None):
        match = np.isclose(a, b, rtol=1e-20, atol=1e-15)
        if not match:
            msg = self._formatMessage(msg, "{} is not close to {}".format(a, b))
            raise self.failureException(msg)

    def _test_arc(self, start, finish, center, direction, title):

        self.queue_mock.reset()

        offset = {'I': center['X'] - start['X'], 'J': center['Y'] - start['Y']}

        gcodes = [
            'G17',
            self._build_start_code(start),
            self._build_curve_code(finish, offset, direction)
        ]

        for gcode in gcodes:
            self.gcode_processor.execute(Gcode({"message": gcode, "prot": "testing"}))

        queue_mock = self.redeem.printer.path_planner.native_planner.queueMove
        queued_points = [args[0][1] for args in queue_mock.call_args_list]

        # pop the G1 positioning command (start point)
        initial = queued_points.pop(0)

        points = [(point[0]*1000, (point[1]*1000)) for point in queued_points]

        if show_plots:
            self._show_plot(start, finish, center, points, title)

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
        start = {'X': -25, 'Y': 0}
        end = {'X': -8, 'Y': 21.464}
        center = {'X': -8, 'Y': 4}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_2_ccw')

    def test_full_circle_ccw(self):
        start = {'Y': 10, 'X': 0}
        end = {'Y': 10, 'X': 0}
        center = {'Y': 10, 'X': 7.5}

        self._test_arc(start, end, center, self.CCW, 'test_full_circle_ccw')

    def test_full_circle_cw(self):
        start = {'Y': 10, 'X': 0}
        end = {'Y': 10, 'X': 0}
        center = {'Y': 10, 'X': 7.5}

        self._test_arc(start, end, center, self.CW, 'test_full_circle_cw')

    def test_inverted_start_end_point_ccw(self):
        start = {'Y': -2, 'X': 7}
        end = {'Y': -6, 'X': -7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CCW, 'test_inverted_start_end_point_ccw')

    def test_inverted_start_end_point_cw(self):
        start = {'Y': -2, 'X': 7}
        end = {'Y': -6, 'X': -7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CW, 'test_inverted_start_end_point_cw')

    def test_machinenet_example_cw(self):
        start = {'Y': 10.0, 'X': 0.0}
        end = {'Y': 15.303, 'X': 12.803}
        center = {'Y': 10.0, 'X': 7.5}

        self._test_arc(start, end, center, self.CW, 'test_machinenet_example_cw')

    def test_quarter_circle_quadrant_1_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': 12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CCW, 'test_quarter_circle_quadrant_1_ccw')

    def test_quarter_circle_quadrant_1_cw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': 12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CW, 'test_quarter_circle_quadrant_1_cw')

    def test_start_quadrant_3_end_quadrant_1_ccw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': 11, 'X': 4.481}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_1_ccw')

    def test_start_quadrant_3_end_quadrant_1_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': 11, 'X': 4.481}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CW, 'test_start_quadrant_3_end_quadrant_1_cw')

    def test_quadrant_3_end_quadrant_2_ccw(self):
        start = {'Y': 0, 'X': -25}
        end = {'Y': 21.464, 'X': -8}
        center = {'Y': 4, 'X': -8}

        self._test_arc(start, end, center, self.CCW, 'test_quadrant_3_end_quadrant_2_ccw')

    def test_quadrant_3_end_quadrant_2_cw(self):
        start = {'Y': 0, 'X': -25}
        end = {'Y': 21.464, 'X': -8}
        center = {'Y': 4, 'X': -8}

        self._test_arc(start, end, center, self.CW, 'test_quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_3_ccw(self):
        start = {'Y': -12, 'X': -14}
        end = {'Y': -14.2, 'X': -8}
        center = {'Y': 6, 'X': -4}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_3_ccw')

    def test_start_quadrant_3_end_quadrant_3_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -7.1, 'X': -4}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_ccw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -2, 'X': 7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CCW, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_4_cw(self):
        start = {'Y': -6, 'X': -7}
        end = {'Y': -2, 'X': 7}
        center = {'Y': 3, 'X': -2}

        self._test_arc(start, end, center, self.CW, 'test_start_quadrant_3_end_quadrant_4_cw')

    def test_three_quarter_circle_quadrant_2_ccw(self):
        start = {'Y': 12.0, 'X': 0.0}
        end = {'Y': 0, 'X': -12}
        center = {'Y': 0.0, 'X': 0.0}

        self._test_arc(start, end, center, self.CCW, 'test_three_quarter_circle_quadrant_2_ccw')




    # def test_basic_G2(self):
    #
    #     '''machinenet example, same as in `test_arc_path_approximation.test_machinenet_example_cw`'''
    #
    #
    #     gcodes = [
    #         'G17',  # set the XY plane
    #         'G1 Y10.0 F8.0',  # set (move) the initial point
    #         'G2 X12.803 Y15.303 I7.50'  # execute the G2 command
    #     ]
    #
    #     for gcode in gcodes:
    #         self.gcode_processor.execute(Gcode({"message": gcode, "prot": "testing"}))
    #
    #     queue_mock = self.redeem.printer.path_planner.native_planner.queueMove
    #     queued_points = [args[0][1] for args in queue_mock.call_args_list]
    #
    #     # pop the G1 positioning command (start point)
    #     start = queued_points.pop(0)
    #
    #     # `test_arc_path_approximation` tests the arc generation. assert correct number of points gets generated
    #     self.assertEqual(len(queued_points), 17)
    #
    #
    #

