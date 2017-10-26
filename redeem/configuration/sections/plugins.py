from redeem.configuration.sections import BaseConfig


class HPX2MaxPluginConfig(BaseConfig):

    # Configuration for the HPX2Max plugin (if loaded)
    # The channel on which the servo is connected. The numbering correspond to the Fan number
    servo_channel = 1

    # Extruder 0 angle to set the servo when extruder 0 is selected, in degree
    extruder_0_angle = 20

    # Extruder 1 angle to set the servo when extruder 1 is selected, in degree
    extruder_1_angle = 175


class DualServoPluginConfig(BaseConfig):

    # Configuration for the Dual extruder by servo plugin
    # This config is only used if loaded.

    # The pin name of where the servo is located
    servo_channel = "P9_14"
    pulse_min = 0.001
    pulse_max = 0.002
    angle_min = -90
    angle_max = 90
    extruder_0_angle = -5
    extruder_1_angle = 5

