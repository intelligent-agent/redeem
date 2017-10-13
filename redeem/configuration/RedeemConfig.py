from redeem.configuration.sections.coldends import ColdendsConfig
from redeem.configuration.sections.delta import DeltaConfig
from redeem.configuration.sections.endstops import EndstopsConfig
from redeem.configuration.sections.fans import FansConfig
from redeem.configuration.sections.geometry import GeometryConfig
from redeem.configuration.sections.heaters import HeatersConfig
from redeem.configuration.sections.planner import PlannerConfig
from redeem.configuration.sections.stepper import StepperConfig
from redeem.configuration.sections.system import SystemConfig


class RedeemConfig(object):
    """match the 'interface' for the ConfigParser to minimize the need
    to make changes where `printer.config` is accessed in the code base.
    """

    system = SystemConfig()



    stepper = StepperConfig()
    planner = PlannerConfig()
    # system = SystemConfig
    # ....

    def get(self, section, key):
        if hasattr(self, section.lower()):
            return getattr(self, section.lower()).get(key)
        return None

    def getint(self, section, key):
        if hasattr(self, section.lower()):
            return getattr(self, section.lower()).getint(key)
        return None

    def getfloat(self, section, key):
        if hasattr(self, section.lower()):
            return getattr(self, section.lower()).getfloat(key)
        return None

    # .
    # .
    # .