try:  # TODO: remove when migrate to python 3
    from confingparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser


from redeem.configuration.RedeemConfig import RedeemConfig
from redeem.configuration.sections.alarms import AlarmsConfig
from redeem.configuration.sections.coldends import ColdendsConfig
from redeem.configuration.sections.delta import DeltaConfig
from redeem.configuration.sections.endstops import EndstopsConfig
from redeem.configuration.sections.fans import FansConfig
from redeem.configuration.sections.filamentsensors import FilamentSensorsConfig
from redeem.configuration.sections.geometry import GeometryConfig
from redeem.configuration.sections.heaters import HeatersConfig
from redeem.configuration.sections.homing import HomingConfig
from redeem.configuration.sections.macros import MacrosConfig
from redeem.configuration.sections.planner import PlannerConfig
from redeem.configuration.sections.plugins import HPX2MaxPluginConfig, DualServoPluginConfig
from redeem.configuration.sections.probe import ProbeConfig
from redeem.configuration.sections.rotaryencoders import RotaryEncodersConfig
from redeem.configuration.sections.servos import ServosConfig
from redeem.configuration.sections.steppers import SteppersConfig
from redeem.configuration.sections.system import SystemConfig
from redeem.configuration.sections.watchdog import WatchdogConfig

import logging


def _clean(key):
    return key.replace('-', '_').lower()


class ConfigFactory(object):

    sections = {
        'Alarms': AlarmsConfig,
        'Cold-ends': ColdendsConfig,
        'Delta': DeltaConfig,
        'Endstops': EndstopsConfig,
        'Fans': FansConfig,
        'Filament-sensors': FilamentSensorsConfig,
        'Geometry': GeometryConfig,
        'Heaters': HeatersConfig,
        'Homing': HomingConfig,
        'Macros': MacrosConfig,
        'Planner': PlannerConfig,
        'HPX2MaxPlugin': HPX2MaxPluginConfig,
        'DualServoPlugin': DualServoPluginConfig,
        'Probe': ProbeConfig,
        'Rotary-encoders': RotaryEncodersConfig,
        'Servos': ServosConfig,
        'Steppers': SteppersConfig,
        'System': SystemConfig,
        'Watchdog': WatchdogConfig
    }

    def __init__(self):
        pass

    def hydrate_config(self, config_file=None, config_files=()):
        """Use default mapper, unless another one is specified by subclass"""
        config_parser = ConfigParser()

        if config_file is not None and len(config_files) > 0:
            raise Exception("cannot provide both single and list of config files")

        if config_file:
            config_parser.read([config_file, ])
        elif len(config_files) > 0:
            num_files = config_parser.read(config_files)
            if num_files < len(config_files):
                logging.warn("number of files loaded less than provided: {} vs. {}".format(num_files, len(config_files)))

        redeem_config = RedeemConfig()

        for section in config_parser.sections():
            if section not in self.sections.keys():
                logging.warn("[{}] does not match known section".format(section))
                continue
            section_cls = self.sections[section]
            hydration_name = 'hydrate_' + section_cls.__name__.lower()
            if hasattr(self, hydration_name):
                config_func = getattr(self, hydration_name)
                config = config_func(config_parser)
            else:
                config = self.hydrate_section_config(config_parser, section, section_cls)
            assert(hasattr(redeem_config, _clean(section)))
            setattr(redeem_config, _clean(section), config)
        return redeem_config

    def hydrate_section_config(self, config_parser, section, config_cls):
        """A simple one-to-one mapper from ini to config class"""
        config = config_cls()
        for option in config_parser.options(section):
            if not config.has(option):
                logging.warn("[{}] '{}' does not match known option".format(section, option))
                continue
            setattr(config, option, config_parser.get(section, option))
        return config
