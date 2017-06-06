import unittest

from redeem.gcodes.M574 import M574

class TestM574(unittest.TestCase):

    def test_build_config(self):
        # no directions -> no config
        self.assertEqual(M574.build_config([]), '')

        # old-style syntax
        self.assertEqual(M574.build_config(['X', 'N', 'E', 'G']), 'x_neg,')
        self.assertEqual(M574.build_config(['Y', 'P', 'O', 'S']), 'y_pos,')
        self.assertEqual(M574.build_config(['Y', 'P', 'O', 'S', 'X', 'P', 'O', 'S']),
                         'y_pos,x_pos,')
        
        # new-style syntax
        self.assertEqual(M574.build_config(['Y-1']), 'y_neg,')
        self.assertEqual(M574.build_config(['Z1']), 'z_pos,')
        self.assertEqual(M574.build_config(['Z1', 'X-1', 'A1']), 'z_pos,x_neg,a_pos,')

        # mixed syntax
        self.assertEqual(M574.build_config(['X', 'N', 'E', 'G', 'Z1']), 'x_neg,z_pos,')
        self.assertEqual(M574.build_config(['Z-1', 'X', 'P', 'O', 'S']), 'z_neg,x_pos,')

        # unsupported non-directional endstops
        self.assertRaisesRegexp(ValueError, "Non-directional.*", M574.build_config, (['X0']))
        self.assertRaisesRegexp(ValueError, "Non-directional.*", M574.build_config, (['Y1', 'Y0']))
        self.assertRaisesRegexp(ValueError, "Non-directional.*",
                                M574.build_config, (['Y', 'P', 'O', 'S', 'Z0']))

        # bad suffixes
        self.assertRaisesRegexp(ValueError, "Can't parse endstop direction suffix.*",
                                M574.build_config, (['Y', 'A', 'L', 'L']))
        self.assertRaisesRegexp(ValueError, "Can't parse endstop direction suffix.*",
                                M574.build_config, (['Y-1', 'X', 'N', 'E', 'S']))
        self.assertRaisesRegexp(ValueError, "Can't parse endstop direction suffix.*",
                                M574.build_config,
                                (['B1', 'X', 'P', 'O', 'S', 'Z', 'C', 'O', 'B']))
        
        # invalid axes
        self.assertRaisesRegexp(ValueError, "Invalid endstop axis.*",
                                M574.build_config, (['G-1']))
        self.assertRaisesRegexp(ValueError, "Invalid endstop axis.*",
                                M574.build_config, (['T', 'P', 'O', 'S']))
        self.assertRaisesRegexp(ValueError, "Invalid endstop axis.*",
                                M574.build_config, (['Y1', 'Q-1']))
        self.assertRaisesRegexp(ValueError, "Invalid endstop axis.*",
                                M574.build_config, (['Y', 'P', 'O', 'S', 'U', 'N', 'E', 'G']))


if __name__ == '__main__':
    unittest.main()