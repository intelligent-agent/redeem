from redeem.configuration.sections import BaseConfig


class HomingConfig(BaseConfig):
    # default G28 homing axes
    g28_default_axes = "X,Y,Z,E,H,A,B,C"

    # Homing speed for the steppers in m/s
    #   Search to minimum ends by default. Negative value for searching to maximum ends.
    home_speed_x = 0.1
    home_speed_y = 0.1
    home_speed_z = 0.1
    home_speed_e = 0.01
    home_speed_h = 0.01
    home_speed_a = 0.01
    home_speed_b = 0.01
    home_speed_c = 0.01

    # homing backoff speed
    home_backoff_speed_x = 0.01
    home_backoff_speed_y = 0.01
    home_backoff_speed_z = 0.01
    home_backoff_speed_e = 0.01
    home_backoff_speed_h = 0.01
    home_backoff_speed_a = 0.01
    home_backoff_speed_b = 0.01
    home_backoff_speed_c = 0.01

    # homing backoff dist
    home_backoff_offset_x = 0.01
    home_backoff_offset_y = 0.01
    home_backoff_offset_z = 0.01
    home_backoff_offset_e = 0.01
    home_backoff_offset_h = 0.01
    home_backoff_offset_a = 0.01
    home_backoff_offset_b = 0.01
    home_backoff_offset_c = 0.01

    # Where should the printer goes after homing.
    # The default is to stay at the offset position.
    # This setting is useful if you have a delta printer
    # and want it to stay at the top position after homing, instead
    # of moving down to the center of the plate.
    # In that case, use home_z and set that to the same as the offset values
    # for X, Y, and Z, only with different sign.
    home_x = 0.0
    home_y = 0.0
    home_z = 0.0
    home_e = 0.0
    home_h = 0.0
    home_a = 0.0
    home_b = 0.0
    home_c = 0.0
