#!/usr/bin/python
# Example taken from http://stackoverflow.com/questions/11331854/how-can-i-generate-an-arc-in-numpy

from numpy import cos,sin,arccos
import numpy as np

def parametric_circle(t,xc,yc,R):
    x = xc + R*cos(t)
    y = yc + R*sin(t)
    return x, y

def inv_parametric_circle(x,xc,R):
    t = arccos((x-xc)/R)
    return t

N = 30
#R = 0.750
x0 = 0.0
y0 = 10.0

x1 = 12.803
y1 = 15.303 
i = 7.50
j = 0.0



x0 = 0
y0 = 1

x1 = 1.2803
y1 = 1.5303

i = 0.750
j = 0

R = np.sqrt(i**2 + j**2)

xc = x0 + i
yc = y0 + j


x0_origin = x0 - xc
y0_origin = y0 - yc

x1_origin = x1 - xc
y1_origin = y1 - yc


ys = (y0_origin, y1_origin)
xs = (x0_origin, x1_origin)

start_theta, end_theta = np.arctan2(ys, xs)


print("start / end thetas: {}, {}".format(start_theta, end_theta))

##
# circumference = 2 * np.pi * R
# arc_angle = (end_theta-start_theta) / 2*pi
# arc_length = circumference * arc_angle
# arc_length = 2 * np.pi * R * (end_theta-start_theta) / 2 * np.pi
# arc_length = R * (end_theta - start_theta)
# N = arc_length / ARC_MOVEMENT

N = 30

arc_thetas = np.linspace(start_theta, end_theta, N)

print("arc thetas: {}".format(arc_thetas))

arc_x, arc_y = parametric_circle(arc_thetas, xc, yc, R)

import matplotlib.pyplot as plt

colors_arc = (0, 0, 0)
color_start = (1, 0, 0)
color_end = (0,1, 0)
color_center = (0, 0, 1)
area = np.pi * 3

# Plot
plt.scatter(arc_x, arc_y, s=3, c=colors_arc, alpha=0.5)
plt.scatter((x0), (y0), s=100, c=color_start, alpha=1, marker='h')
plt.scatter((x1), (y1), s=100, c=color_end, alpha=1, marker='h')
plt.scatter((xc), (yc), s=100, c=color_center, alpha=1, marker='h')
plt.show()


#
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