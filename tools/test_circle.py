#!/usr/bin/env python
import unittest
import numpy as np
import matplotlib.pyplot as plt
# import sympy as sp

#
# def parametric_circle(t,xc,yc,R):
#     x = xc + R * np.cos(t)
#     y = yc + R * np.sin(t)
#     return x, y


def find_circle_center(x1, y1, x2, y2, r):

    c1 = sp.Circle(sp.Point(x1, y1), abs(r))
    c2 = sp.Circle(sp.Point(x2, y2), abs(r))

    intersection = c1.intersection(c2)

    if len(intersection) < 1:
        raise Exception("radius circles do not intersect")
    if len(intersection) < 2 or r > 0:  # single intersection or "positive" radius center point
        return intersection[0].x, intersection[0].y
    return intersection[1].x, intersection[1].y # "negative" radius center point


def create_arc_segments(x0, y0, x1, y1, i, j, cw=True):

    R = np.sqrt(i ** 2 + j ** 2)

    xc = x0 + i
    yc = y0 + j

    x0_origin = x0 - xc
    y0_origin = y0 - yc

    x1_origin = x1 - xc
    y1_origin = y1 - yc

    ys = (y0_origin, y1_origin)
    xs = (x0_origin, x1_origin)

    start_theta, end_theta = np.arctan2(ys, xs)

    ''' clockwise => theta always decreasing'''
    ''' counterclockwise => theta always increasing'''

    ''' in order to use linspace, cw motion needs start theta greater than end theta. if not, need to correct'''
    ''' for ccw motion if start theta is not less than end theta, need to correct'''

    ''' since it's modulo pi, we can adjust by using the distance from +/- pi'''

    if start_theta <= end_theta and cw:
        start_theta = np.pi + abs(-np.pi - start_theta)

    if start_theta >= end_theta and not cw:
        start_theta = -np.pi - abs(np.pi - start_theta)

    # print("start {} end {}".format(start_theta, end_theta))

    arc_length = R * abs(end_theta - start_theta)
    num_segments = int(arc_length / 0.25)

    arc_thetas = np.linspace(start_theta, end_theta, num_segments)

    arc_x = xc + R * np.cos(arc_thetas)
    arc_y = yc + R * np.sin(arc_thetas)

    return arc_x, arc_y


def show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, title=None):

    xc = x0 + i
    yc = y0 + j

    print("def {}(self):".format(title))
    print("start = {}".format({'X': x0, 'Y': y0}))
    print("end = {}".format({'X': x1, 'Y': y1}))
    print("center = {}".format({'X': xc, 'Y': yc}))




    colors_arc = (0, 0, 0)
    color_start = (0, 1, 0)
    color_end = (1,0, 0)
    color_center = (0, 0, 1)
    area = np.pi * 3

    # Plot
    plt.scatter(arc_x, arc_y, s=20, c=colors_arc, alpha=0.5)
    plt.scatter((x0), (y0), s=300, c=color_start, alpha=1, marker='h')
    plt.scatter((x1), (y1), s=100, c=color_end, alpha=1, marker='h')
    plt.scatter((xc), (yc), s=100, c=color_center, alpha=1, marker='h')

    if title:
        plt.title(title)

    # plt.show()


class TestArcSegments(unittest.TestCase):

    def test_machinenet_example(self):
        x0 = 0.0
        y0 = 1.0

        x1 = 1.2803
        y1 = 1.5303
        i = 0.750
        j = 0.0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, title="machinenet example cw")

    def test_start_quadrant_3_end_quadrant_2_cw(self):
        x0 = -25
        y0 = 0

        x1 = -8
        y1 = 21.464

        i = 17
        j = 4

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, title='quadrant_3_end_quadrant_2_cw')

    def test_start_quadrant_3_end_quadrant_2_ccw(self):
        x0 = -25
        y0 = 0

        x1 = -8
        y1 = 21.464

        i = 17
        j = 4

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, title='quadrant_3_end_quadrant_2_ccw')

    def test_start_quadrant_3_end_quadrant_4_cw(self):
        x0 = -7
        y0 = -6

        x1 = 7
        y1 = -2

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_4_cw')

    def test_start_quadrant_3_end_quadrant_4_ccw(self):
        x0 = -7
        y0 = -6

        x1 = 7
        y1 = -2

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_4_ccw')

    def test_start_quadrant_3_end_quadrant_1_cw(self):
        x0 = -7
        y0 = -6

        x1 = 4.481
        y1 = 11

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_1_cw')

    def test_start_quadrant_3_end_quadrant_1_ccw(self):
        x0 = -7
        y0 = -6

        x1 = 4.481
        y1 = 11

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_1_ccw')

    def test_start_quadrant_3_end_quadrant_3_cw(self):
        x0 = -7
        y0 = -6

        x1 = -4
        y1 = -7.1

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_3_cw')

    def test_start_quadrant_3_end_quadrant_3_ccw(self):
        x0 = -7
        y0 = -6

        x1 = -4
        y1 = -7.1

        i = 5
        j = 9

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_start_quadrant_3_end_quadrant_3_ccw')

    def test_quarter_circle_quadrant_1_cw(self):
        x0 = 0.0
        y0 = 12.0

        x1 = 12
        y1 = 0

        i = 0
        j = -12.0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_quarter_circle_quadrant_1_cw')

    def test_quarter_circle_quadrant_1_ccw(self):
        x0 = 0.0
        y0 = 12.0

        x1 = 12
        y1 = 0

        i = 0
        j = -12.0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_quarter_circle_quadrant_1_ccw')

    def test_three_quarter_circle_quadrant_2_ccw(self):
        x0 = 0.0
        y0 = 12.0

        x1 = -12
        y1 = 0

        i = 0
        j = -12.0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_three_quarter_circle_quadrant_2_ccw')

    def test_inverted_start_end_point_cw(self):
        x0 = 7
        y0 = -2

        x1 = -7
        y1 = -6

        i = -9
        j = 5

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_inverted_start_end_point_cw')

    def test_inverted_start_end_point_ccw(self):
        x0 = 7
        y0 = -2

        x1 = -7
        y1 = -6

        i = -9
        j = 5

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_inverted_start_end_point_ccw')

    def test_full_circle_cw(self):
        x0 = 0
        y0 = 1

        x1 = 0
        y1 = 1

        i = 0.750
        j = 0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=True)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_full_circle_cw')

    def test_full_circle_ccw(self):
        x0 = 0
        y0 = 1

        x1 = 0
        y1 = 1

        i = 0.750
        j = 0

        arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, i, j, cw=False)
        show_plot(x0, y0, x1, y1, i, j, arc_x, arc_y, 'test_full_circle_ccw')

    # def test_inverted_start_end_point_cw_positive_radius_version(self):
    #     x0 = 7
    #     y0 = -2
    #
    #     x1 = -7
    #     y1 = -6
    #
    #     i = -9
    #     j = 5
    #
    #     r = np.sqrt(i**2 + j**2)
    #
    #     xc, yc = find_circle_center(x0, y0, x1, y1, r)
    #
    #     # calculate i and j
    #     derived_i = x0 - xc
    #     derived_j = y0 - yc
    #
    #     self.assertEqual(derived_i, i)
    #     self.assertEqual(derived_j, j)
    #
    #     arc_x, arc_y = create_arc_segments(x0, y0, x1, y1, derived_i, derived_j, cw=True)
    #     show_plot(x0, y0, x1, y1, derived_i, derived_j, arc_x, arc_y, 'test_inverted_start_end_point_cw')


if __name__ == '__main__':
    unittest.main()



#
# N = 30
# #R = 0.750
# x0 = 0.0
# y0 = 10.0
#
# x1 = 12.803
# y1 = 15.303
# i = 7.50
# j = 0.0
#
#
#
# x0 = 0
# y0 = 1
#
# x1 = 1.2803
# y1 = 1.5303
#
# i = 0.750
# j = 0
#
#
# print("start / end thetas: {}, {}".format(start_theta, end_theta))
#
# ##
# # circumference = 2 * np.pi * R
# # arc_angle = (end_theta-start_theta) / 2*pi
# # arc_length = circumference * arc_angle
# # arc_length = 2 * np.pi * R * (end_theta-start_theta) / 2 * np.pi
# # arc_length = R * (end_theta - start_theta)
# # N = arc_length / ARC_MOVEMENT
#
# N = 30
#
# arc_thetas = np.linspace(start_theta, end_theta, N)
#
# print("arc thetas: {}".format(arc_thetas))
#
# arc_x, arc_y = parametric_circle(arc_thetas, xc, yc, R)
#
# import matplotlib.pyplot as plt
#
# colors_arc = (0, 0, 0)
# color_start = (1, 0, 0)
# color_end = (0,1, 0)
# color_center = (0, 0, 1)
# area = np.pi * 3
#
# # Plot
# plt.scatter(arc_x, arc_y, s=3, c=colors_arc, alpha=0.5)
# plt.scatter((x0), (y0), s=100, c=color_start, alpha=1, marker='h')
# plt.scatter((x1), (y1), s=100, c=color_end, alpha=1, marker='h')
# plt.scatter((xc), (yc), s=100, c=color_center, alpha=1, marker='h')
# plt.show()
#
#
# #
#
#
#
#
#
#
#
#
#
# #start_point = (xc + R*cos(.3), yc + R*sin(.3))
# #end_point   = (xc + R*cos(2.2), yc + R*sin(2.2))
#
# start_point = (x0, y0)
# end_point   = (x1, y1)
#
#
# length = np.sqrt( (x1-x0)**2 + (y1-y0)**2 )
#
#
# angle = np.arctan(length / R)
# arc_length = np.pi * R * np.arctan(length/R)
# # circumference = 2 * np.pi * R
#
# # arc_length = circumference * angle / 360
#
# #
# # print("angle: {}".format(angle))
# # print("arc length: {}".format(arc_length))
#
#
# start_t = inv_parametric_circle(start_point[0], i, R)
# end_t   = inv_parametric_circle(end_point[0], i, R)
#
# print start_t
# print end_t
#
#
#
# arc_T = np.linspace(start_t, end_t+2*np.pi, N)
#
# arc_I = np.linspace(start_t, end_t, N)
#
# print("{}".format(arc_T))
#
# # from pylab import *
# X,Y = parametric_circle(arc_T, start_point[0]+i, start_point[1]+j, R)
# J, K = parametric_circle(arc_I, start_point[0]+i, start_point[1]+j, R)
#
# # print("{} || {}".format(X, Y))
#
# # plot(X,Y)
# # scatter(X,Y)
# # scatter([x0+i],[y0+j],color='r',s=100)
# # axis('equal')
# # show()
#
# # import matplotlib.pyplot as plt
# #
# # colors= (0,0,0)
# # area = np.pi*3
# # #
# # plt.scatter(X,Y)
# # # plt.show()
# #
#
#
# import numpy as np
# import matplotlib.pyplot as plt
#
# # Create data
# N = 30
# x = np.random.rand(N)
# y = np.random.rand(N)
# colorsXY = (0, 0, 0)
# colorsJK = (1, 0, 0)
# area = np.pi * 3
#
# # Plot
# plt.scatter(X, Y, s=area, c=colorsXY, alpha=0.5)
# # plt.scatter(J, K, s=area, c=colorsJK, alpha=0.5)
# plt.title('Scatter plot pythonspot.com')
# plt.xlabel('x')
# plt.ylabel('y')
# plt.show()