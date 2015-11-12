# Example taken from http://stackoverflow.com/questions/11331854/how-can-i-generate-an-arc-in-numpy

from numpy import cos,sin,arccos
import numpy as np

def parametric_circle(t,xc,yc,R):
    x = xc + R*cos(t)
    y = yc + R*sin(t)
    return x,y

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

R = np.sqrt(i**2 + j**2)

#start_point = (xc + R*cos(.3), yc + R*sin(.3))
#end_point   = (xc + R*cos(2.2), yc + R*sin(2.2))

start_point = (x0, y0)
end_point   = (x1, y1)


start_t = inv_parametric_circle(start_point[0], start_point[0]+i, R)
end_t   = inv_parametric_circle(end_point[0], start_point[0]+i, R)

arc_T = np.linspace(start_t, end_t, N)

from pylab import *
X,Y = parametric_circle(arc_T, start_point[0]+i, start_point[1]+j, R)
plot(X,Y)
scatter(X,Y)
scatter([x0+i],[y0+j],color='r',s=100)
axis('equal')
show()
