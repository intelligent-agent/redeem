from redeem.CascadingConfigParser import CascadingConfigParser
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


class ConfigFactory(object):
    cpp = None
    sections = [
        ('Alarms', AlarmsConfig),
        ('Cold-ends', ColdendsConfig),
        ('Delta', DeltaConfig),
        ('Endstops', EndstopsConfig),
        ('Fans', FansConfig),
        ('Filament-sensors', FilamentSensorsConfig),
        ('Geometry', GeometryConfig),
        ('Heaters', HeatersConfig),
        ('Homing', HomingConfig),
        ('Macros', MacrosConfig),
        ('Planner', PlannerConfig),
        ('HPX2MaxPlugin', HPX2MaxPluginConfig),
        ('DualServoPlugin', DualServoPluginConfig),
        ('Probe', ProbeConfig),
        ('Rotary-encoders', RotaryEncodersConfig),
        ('Servos', ServosConfig),
        ('Steppers', SteppersConfig),
        ('System', SystemConfig),
        ('Watchdog', WatchdogConfig)
    ]

    def __init__(self, config_files):
        self.ccp = CascadingConfigParser(config_files)

    def hydrate_config(self):
        """Use default mapper, unless another one is specified by subclass"""
        redeem_config = RedeemConfig()
        for section_name, section_cls in self.sections:
            hydration_name = 'hydrate_' + section_cls.__name__.lower()
            if hasattr(self, hydration_name):
                config_func = getattr(self, hydration_name)
                config = config_func()
            else:
                config = self.hydrate_section_config(section_name, section_cls)
            setattr(redeem_config, section_name.lower(), config)
        return redeem_config

    def hydrate_section_config(self, section_name, config_cls):
        """A simple one-to-one mapper from ini to config class"""
        config = config_cls()
        for item in config_cls.__dict__:
            if item.startswith('__'):
                continue
            setattr(config, item, self.ccp.get(section_name, item))
        return config
