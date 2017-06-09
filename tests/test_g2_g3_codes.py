from unittest import TestCase

from redeem.Gcode import Gcode
from redeem.Redeem import Redeem

from mock import patch, Mock


class G2G3CodesTest(TestCase):

    def setUp(self):
        self.patcher = patch('redeem.path_planner.PathPlannerNative.PathPlannerNative')
        self.queue_mock = self.patcher.start()

        self.redeem = Redeem("/usr/src/redeem/configs")
        self.redeem.printer.enable.set_enabled()
        self.gcode_processor = self.redeem.printer.processor

        # the native planner handles processing the paths
        # create mock so that replicape doesn't send the paths to any connected stepper motors
        self.redeem.printer.path_planner.native_planner = Mock()

    def tearDown(self):
        self.redeem.exit()

    def test_basic_G2(self):

        '''machinenet example, same as in `test_arc_path_approximation.test_machinenet_example_cw`'''

        gcodes = [
            'G17',  # set the XY plane
            'G1 Y10.0 F8.0',  # set (move) the initial point
            'G2 X12.803 Y15.303 I7.50'  # execute the G2 command
        ]

        for gcode in gcodes:
            self.gcode_processor.execute(Gcode({"message": gcode, "prot": "testing"}))

        queue_mock = self.redeem.printer.path_planner.native_planner.queueMove
        queued_points = [args[0][1] for args in queue_mock.call_args_list]

        # pop the G1 positioning command (start point)
        start = queued_points.pop(0)

        # `test_arc_path_approximation` tests the arc generation. assert correct number of points gets generated
        self.assertEqual(len(queued_points), 17)




