import numpy as np

from redeem.configuration.factories import ConfigFactory
from redeem.configuration.sections.delta import DeltaConfig


def _getfloat(config_parser, section, option, default):
    if config_parser.has_option(section, option):
        return config_parser.getfloat(section, option)
    return default

def _degreesToRadians(radians):
    return radians * 180 / np.pi


class ConfigFactoryV19(ConfigFactory):

    def _calc_old_column_position(self, r,
                                  ae, be, ce,
                                  a_tangential, b_tangential, c_tangential,
                                  a_radial, b_radial, c_radial):
        """from https://github.com/intelligent-agent/redeem/blob/5f225ddf3ab806ef8996e1431bbef6c454a60f48/redeem/path_planner/Delta.cpp"""  # noqa

        # Column theta
        At = np.pi / 2.0
        Bt = 7.0 * np.pi / 6.0
        Ct = 11.0 * np.pi / 6.0

        # Calculate the column tangential offsets
        Apxe = a_tangential   # Tower A doesn't require a separate y componen
        Apye = 0.00
        Bpxe = b_tangential / 2.0
        Bpye = np.sqrt(3.0)*(-b_tangential/2.0)
        Cpxe = np.sqrt(3.0)*(c_tangential/2.0)
        Cpye = c_tangential/2.0

        # Calculate the column positions
        Apx = (a_radial + r) * np.cos(At) + Apxe
        Apy = (a_radial + r) * np.sin(At) + Apye
        Bpx = (b_radial + r) * np.cos(Bt) + Bpxe
        Bpy = (b_radial + r) * np.sin(Bt) + Bpye
        Cpx = (c_radial + r) * np.cos(Ct) + Cpxe
        Cpy = (c_radial + r) * np.sin(Ct) + Cpye

        # Calculate the effector positions
        Aex = ae * np.cos(At)
        Aey = ae * np.sin(At)
        Bex = be * np.cos(Bt)
        Bey = be * np.sin(Bt)
        Cex = ce * np.cos(Ct)
        Cey = ce * np.sin(Ct)

        # Calculate the virtual column positions
        Avx = Apx - Aex
        Avy = Apy - Aey
        Bvx = Bpx - Bex
        Bvy = Bpy - Bey
        Cvx = Cpx - Cex
        Cvy = Cpy - Cey

        return Avx, Avy, Bvx, Bvy, Cvx, Cvy

    def _calc_new_column_position(self, r, Avx, Avy, Bvx, Bvy, Cvx, Cvy):
        """
        from new calcs


        1) Avx = (A_radial + r)*cos(At);
        2) Avy = (A_radial + r)*sin(At);

        solve for a_radial
        3) (Avx / cos(At)) - r = A_radial
        4) (Avy / sin(At)) - r = A_radial

        set 3 equal to 4
        5) Avy / Avx = sin(At) / cos(At) = tan(At)

        solve for At
        6) arctan(Avy/Avx) = At

        a_radial from 6 into 1
        """

        At = np.arctan(Avy / Avx)
        Bt = np.arctan(Bvy / Bvx)
        Ct = np.arctan(Cvy / Cvx)

        a_radial = (Avx / np.cos(At)) - r
        b_radial = (Bvx / np.cos(Bt)) - r
        c_radial = (Cvx / np.cos(Ct)) - r

        '''from new calcs
        At = degreesToRadians(90.0 + A_angular)
        Bt = degreesToRadians(210.0 + B_angular)
        Ct = degreesToRadians(330.0 + C_angular)'''

        # solve for _angular
        a_angular = _degreesToRadians(At) - 90
        b_angular = _degreesToRadians(Bt) - 210
        c_angular = _degreesToRadians(Ct) - 330

        return a_radial, b_radial, c_radial, a_angular, b_angular, c_angular

    def hydrate_deltaconfig(self, config_parser):
        """

        1.9 used ae, be, ce along with a/b/c_tangential to calculate position of each tower

        2.0 users angular and radial dimensions


        also r in 1.9 was just radius to edge of effector, instead of the center as in 2.0

        """
        cfg = DeltaConfig()

        # if this isn't a delta config, skip transformations
        if config_parser.getint('geometry', 'axis_config') != 3:
            return cfg


        # length of rod same
        if config_parser.has_option('delta', 'l'):
            cfg.l = config_parser.getfloat('delta', 'l')

        # radius2.0 = radius1.9 + Ae
        if config_parser.has_option('delta', 'r'):
            cfg.r = config_parser.getfloat('delta', 'r')

        if config_parser.has_option('delta', 'ae'):
            cfg.r += config_parser.getfloat('delta', 'ae')

        r = _getfloat(config_parser, 'delta', 'r', 0.0)
        ae = _getfloat(config_parser, 'delta', 'ae', 0.0)
        be = _getfloat(config_parser, 'delta', 'be', 0.0)
        ce = _getfloat(config_parser, 'delta', 'ce', 0.0)
        a_radial = _getfloat(config_parser, 'delta', 'a_radial', 0.0)
        b_radial = _getfloat(config_parser, 'delta', 'b_radial', 0.0)
        c_radial = _getfloat(config_parser, 'delta', 'c_radial', 0.0)
        a_tangential = _getfloat(config_parser, 'delta', 'a_tangential', 0.0)
        b_tangential = _getfloat(config_parser, 'delta', 'b_tangential', 0.0)
        c_tangential = _getfloat(config_parser, 'delta', 'c_tangential', 0.0)

        Avx, Avy, Bvx, Bvy, CvX, Cvy = self._calc_old_column_position(r,
                                                                      ae, be, ce,
                                                                      a_tangential, b_tangential, c_tangential,
                                                                      a_radial, b_radial, c_radial)

        (cfg.a_radial, cfg.b_radial, cfg.c_radial,
         cfg.a_angular, cfg.b_angular, cfg.c_angular) = self._calc_new_column_position(cfg.r,
                                                                                       Avx, Avy,
                                                                                       Bvx, Bvy,
                                                                                       CvX, Cvy)

        return cfg