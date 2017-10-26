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


class RedeemConfig(object):
    """match the 'interface' for the ConfigParser to minimize the need
    to make changes where `printer.config` is accessed in the code base.
    """

    alarms = AlarmsConfig()
    cold_ends = ColdendsConfig()
    delta = DeltaConfig()
    endstops = EndstopsConfig()
    fans = FansConfig()
    filament_sensors = FilamentSensorsConfig()
    geometry = GeometryConfig()
    heaters = HeatersConfig()
    homing = HomingConfig()
    macros = MacrosConfig()
    planner = PlannerConfig()
    hpx2maxplugin = HPX2MaxPluginConfig()
    dualservoplugin = DualServoPluginConfig()
    probe = ProbeConfig()
    rotary_encoders = RotaryEncodersConfig()
    servos = ServosConfig()
    steppers = SteppersConfig()
    system = SystemConfig()
    watchdog = WatchdogConfig()

    def get(self, section, key):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).get(key)
        return None

    def has(self, section, key):
        return hasattr(self, section.replace('-', '_').lower()) and getattr(self, section.replace('-', '_').lower()).has(key)

    def getint(self, section, key):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).getint(key)
        return None

    def getfloat(self, section, key):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).getfloat(key)
        return None
