from redeem.configuration.sections import BaseConfig


class RotaryEncodersConfig(BaseConfig):
    enable_e = False
    event_e = "/dev/input/event1"
    cpr_e = -360
    diameter_e = 0.003
