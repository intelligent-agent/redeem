import struct
import logging
import random
import string

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

    replicape_revision = None
    replicape_data = None
    replicape_path = None
    replicape_key = None

    reach_revision = None
    reach_data = None
    reach_path = None

    def get(self, section, key, default=None):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).get(key)
        return default

    def has(self, section, key):
        return hasattr(self, section.replace('-', '_').lower()) and getattr(self, section.replace('-', '_').lower()).has(key)

    # alias
    def has_option(self, section, key):
        return self.has(section, key)

    def getint(self, section, key, default=None):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).getint(key)
        return default

    def getfloat(self, section, key, default=None):
        if hasattr(self, section.replace('-', '_').lower()):
            return getattr(self, section.replace('-', '_').lower()).getfloat(key)
        return default

    def getboolean(self, section, key, default=None):
        if hasattr(self, section.replace('-','_').lower()):
            return getattr(self, section.replace('-', '_').lower()).getboolean(key)
        return default

    def parse_capes(self):
        """ Read the name and revision of each cape on the BeagleBone """
        self.replicape_revision = None
        self.reach_revision = None

        import glob
        paths = glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/*/nvmem")
        paths.extend(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/nvmem/at24-[1-4]/nvmem"))
        # paths.append(glob.glob("/sys/bus/i2c/devices/[1-2]-005[4-7]/eeprom"))
        for i, path in enumerate(paths):
            try:
                with open(path, "rb") as f:
                    data = f.read(120)
                    name = data[58:74].strip()
                    if name == "BB-BONE-REPLICAP":
                        self.replicape_revision = data[38:42]
                        self.replicape_data = data
                        self.replicape_path = path
                    elif name[:13] == "BB-BONE-REACH":
                        self.reach_revision = data[38:42]
                        self.reach_data = data
                        self.reach_path = path
                    if self.replicape_revision is not None and self.reach_revision is not None:
                        break
            except IOError as e:
                pass

    def save(self, filename):
        raise NotImplemented("not yet implemented")

    def _gen_key(self):
        """ Used to generate a key when one is not found """
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))

    def get_key(self):
        """ Get the generated key from the config or create one """

        self.replicape_key = "".join(struct.unpack('20c', self.replicape_data[100:120]))

        logging.debug("Found Replicape key: '"+self.replicape_key+"'")

        if self.replicape_key == '\x00'*20:
            logging.debug("Replicape key invalid")

            self.replicape_key = self._gen_key()
            self.replicape_data = self.replicape_data[:100] + self.replicape_key

            logging.debug("New Replicape key: '"+self.replicape_key+"'")

            try:
                with open(self.replicape_path, "wb") as f:
                    f.write(self.replicape_data[:120])
            except IOError as e:
                logging.warning("Unable to write new key to EEPROM")
        return self.replicape_key
