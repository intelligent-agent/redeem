from redeem.configuration.sections import BaseConfig


class StepperConfig(BaseConfig):

    microstepping_x, microstepping_y, microstepping_z = 3, 3, 3
    microstepping_e, microstepping_h = 3, 3
    microstepping_a, microstepping_b, microstepping_c = 3, 3, 3

    current_x, current_y, current_z = 0.5, 0.5, 0.5
    current_e, current_h = 0.5, 0.5
    current_a, current_b, current_c = 0.5, 0.5, 0.5

    # full steps per 1 mm, ignore microstepping settings
    steps_pr_mm_x, steps_pr_mm_y, steps_pr_mm_z = 4.0, 4.0, 50.0
    steps_pr_mm_e, steps_pr_mm_h = 6.0, 6.0
    steps_pr_mm_a, steps_pr_mm_b, steps_pr_mm_c = 6.0, 6.0, 6.0

    backlash_x, backlash_y, backlash_z = 0.0, 0.0, 0.0
    backlash_e, backlash_h = 0.0, 0.0
    backlash_a, backlash_b, backlash_c = 0.0, 0.0, 0.0

    # Which steppers are enabled
    in_use_x, in_use_y, in_use_z = True, True, True
    in_use_e, in_use_h = True, True
    in_use_a, in_use_b, in_use_c = False, False, False

    # Set to -1 if axis is inverted
    direction_x, direction_y, direction_z = 1, 1, 1
    direction_e, direction_h = 1, 1
    direction_a, direction_b, direction_c = 1, 1, 1

    # Set to True if slow decay mode is needed
    slow_decay_x, slow_decay_y, slow_decay_z = 0, 0, 0
    slow_decay_e, slow_decay_h = 0, 0
    slow_decay_a, slow_decay_b, slow_decay_c = 0, 0, 0

    # A stepper controller can operate in slave mode,
    # meaning that it will mirror the position of the
    # specified stepper. Typically, H will mirror Y or Z,
    # in the case of the former, write this: slave_y = H.
    slave_x, slave_y, slave_z = None, None, None
    slave_e, slave_h = None, None
    slave_a, slave_b, slave_c = None, None, None

    # Stepper timout
    use_timeout = True
    timeout_seconds = 500

