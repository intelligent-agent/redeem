from redeem.configuration.sections import BaseConfig


class ServosConfig(BaseConfig):

    # Example servo for Rev A4A, connected to channel 14 on the PWM chip
    # For Rev B, servo is either P9_14 or P9_16.
    # Not enabled for now, just kept here for reference.
    # Angle init is the angle the servo is set to when redeem starts.
    # pulse min and max is the pulse with for min and max position, as always in SI unit Seconds.
    # So 0.001 is 1 ms.
    # Angle min and max is what angles those pulses correspond to.
    servo_0_enable = False
    servo_0_channel = "P9_14"
    servo_0_angle_init = 90
    servo_0_angle_min = -90
    servo_0_angle_max = 90
    servo_0_pulse_min = 0.001
    servo_0_pulse_max = 0.002
