from redeem.configuration.sections import BaseConfig


class FilamentSensorsConfig(BaseConfig):

    # If the error is > 1 cm, sound the alarm
    alarm_level_e = 0.01
