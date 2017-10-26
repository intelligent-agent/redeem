import unittest
from ConfigParser import SafeConfigParser, RawConfigParser

import os

from redeem.configuration.RedeemConfig import RedeemConfig
from redeem.configuration.factories.ConfigFactoryV20 import ConfigFactoryV20

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

        files = [
            os.path.join(current_path, 'resources/default.2.0.cfg'),
        ]

        factory = ConfigFactoryV20(files)
        redeem_config = factory.hydrate_config()

        default_cfg = os.path.join(current_path, 'resources/default.2.0.cfg')
        cp = RawConfigParser()
        cp.read(default_cfg)
        self._compare_configs(cp, redeem_config)
