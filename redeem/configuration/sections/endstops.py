from redeem.configuration.sections import BaseConfig


class EndstopsConfig(BaseConfig):

    # Which axis should be homed.
    has_x = True
    has_y = True
    has_z = True
    has_e = False
    has_h = False
    has_a = False
    has_b = False
    has_c = False

    inputdev = '/dev/input/by-path/platform-ocp:gpio_keys-event'

    # Number of cycles to wait between checking
    # end stops. CPU frequency is 200 MHz
    end_stop_delay_cycles = 1000

    # Invert =
    #   True means endstop is connected as Normally Open (NO) or not connected
    #   False means endstop is connected as Normally Closed (NC)
    invert_X1 = False
    invert_X2 = False
    invert_Y1 = False
    invert_Y2 = False
    invert_Z1 = False
    invert_Z2 = False

    pin_X1 = 'GPIO3_21'
    pin_X2 = 'GPIO0_30'
    pin_Y1 = 'GPIO1_17'
    pin_Y2 = 'GPIO3_17'
    pin_Z1 = 'GPIO0_31'
    pin_Z2 = 'GPIO0_4'

    keycode_X1 = 112
    keycode_X2 = 113
    keycode_Y1 = 114
    keycode_Y2 = 115
    keycode_Z1 = 116
    keycode_Z2 = 117

    # If one endstop is hit, which steppers and directions are masked.
    #   The list is comma separated and has format
    #     x_cw = stepper x clockwise (independent of direction_x)
    #     x_ccw = stepper x counter clockwise (independent of direction_x)
    #     x_neg = setpper x negative direction (affected by direction_x)
    #     x_pos = setpper x positive direction (affected by direction_x)
    #   Steppers e and h (and a, b, c for reach) can also be masked.
    #
    #   For a list of steppers to stop, use this format: x_cw, y_ccw
    #   For Simple XYZ bot, the usual practice would be
    #     end_stop_X1_stops = x_neg, end_stop_X2_stops = x_pos, ...
    #   For CoreXY and similar, two steppers should be stopped if an end stop is hit.
    #     similarly for a delta probe should stop x, y and z.
    end_stop_X1_stops = None
    end_stop_Y1_stops = None
    end_stop_Z1_stops = None
    end_stop_X2_stops = None
    end_stop_Y2_stops = None
    end_stop_Z2_stops = None

    # if an endstop should only be used for homing or probing, then add it to
    # homing_only_endstops in comma separated format.
    # Example: homing_only_endstops = Z1, Z2
    #   this will make sure that endstop Z1 and Z2 are only used during homing or probing
    # NOTE: Be very careful with this option.

    homing_only_endstops = None

    soft_end_stop_min_x = -0.5
    soft_end_stop_min_y = -0.5
    soft_end_stop_min_z = -0.5
    soft_end_stop_min_e = -1000.0
    soft_end_stop_min_h = -1000.0
    soft_end_stop_min_a = -1000.0
    soft_end_stop_min_b = -1000.0
    soft_end_stop_min_c = -1000.0

    soft_end_stop_max_x = 0.5
    soft_end_stop_max_y = 0.5
    soft_end_stop_max_z = 0.5
    soft_end_stop_max_e = 1000.0
    soft_end_stop_max_h = 1000.0
    soft_end_stop_max_a = 1000.0
    soft_end_stop_max_b = 1000.0
    soft_end_stop_max_c = 1000.0