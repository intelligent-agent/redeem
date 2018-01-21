from redeem.configuration.sections import BaseConfig


class DeltaConfig(BaseConfig):

    l = 0.135                       # Length of the rod (m)
    r = 0.144                       # Radius of the columns (m)

    # Compensation for positional error of the columns
    # Radial offsets of the columns, positive values move the tower away from the center of the printer (m)
    a_radial, b_radial, c_radial = 0.0, 0.0, 0.0

    # Angular offsets of the columns
    # Positive values move the tower counter-clockwise, as seen from above (degrees)
    a_angular, b_angular, c_angular = 0.0, 0.0, 0.0
