import unittest
from ConfigParser import SafeConfigParser, RawConfigParser

import os

import re

from redeem.configuration.RedeemConfig import RedeemConfig
from redeem.configuration.factories.ConfigFactoryV20 import ConfigFactoryV20
from tests.logger_test import LogTestCase

current_path = os.path.dirname(os.path.abspath(__file__))


class ConfigTests(unittest.TestCase):

    def _compare_configs(self, cp, redeem_config):

        for section in cp.sections():
            for option in cp.options(section):
                self.assertTrue(redeem_config.has(section, option), 'option {}/{} is missing'.format(section, option))

                if section == "Macros":
                    continue

                config_val = str(cp.get(section, option))
                redeem_val = str(redeem_config.get(section, option))
                self.assertEqual(config_val, redeem_val, "option {}/{} does not match: '{}' vs '{}'".format(section, option, config_val, redeem_val))

    def test_all_keys_in_config(self):

        default_cfg = os.path.join(current_path, 'resources/default.2.0.cfg')
        cp = RawConfigParser()
        self.assertEqual(len(cp.read(default_cfg)), 1)

        redeem_config = RedeemConfig()
        self._compare_configs(cp, redeem_config)

    def test_basic_config_factory(self):

        factory = ConfigFactoryV20()
        redeem_config = factory.hydrate_config(config_file=os.path.join(current_path, 'resources/default.2.0.cfg'))

        default_cfg = os.path.join(current_path, 'resources/default.2.0.cfg')
        cp = RawConfigParser()
        cp.read(default_cfg)
        self._compare_configs(cp, redeem_config)


class ConfigWarningTests(LogTestCase):

    known_19_mismatches = ('hez', 'ae', 'be', 'ce', 'a_tangential', 'b_tangential', 'c_tangential', 'min_buffered_move_time', 'max_length', 'min_speed_x', 'min_speed_y', 'min_speed_z', 'min_speed_e', 'min_speed_h', 'min_speed_a', 'min_speed_b', 'min_speed_c',)

    def test_old_config_factory(self):
        """ test to make sure that 1.9 config mismatches the above list"""

        factory = ConfigFactoryV20()

        with self.assertLogs('', level='WARN') as cm:
            factory.hydrate_config(config_file=os.path.join(current_path, 'resources/default.1.9.cfg'))
            for warning in cm.output:
                m = re.search(r'.*?\'([a-z_]+)\'', warning)
                self.assertIsNotNone(m, "needs to match: {}".format(warning))
                self.assertIn(m.group(1), self.known_19_mismatches)


class LoadMultipleConfigs(LogTestCase):

    def test_printer_and_local(self):

        files = [
            os.path.join(current_path, 'resources/printer.cfg'),
            os.path.join(current_path, 'resources/local.cfg')
        ]

        factory = ConfigFactoryV20()
        redeem_config = factory.hydrate_config(config_files=files)

        # make sure local takes precedence
        self.assertEqual(redeem_config.getint('System', 'loglevel'), 30)

