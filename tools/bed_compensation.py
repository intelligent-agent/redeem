"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random

# With reset of probe 
#points = [{'Y': 20.0, 'X': 10.0, 'Z': 0.00068000000000000005}, {'Y': 20.0, 'X': 100.0, 'Z': 0.00038299999999999966}, {'Y': 20.0, 'X': 190.0, 'Z': 0.00045175000000000076}, {'Y': 100.0, 'X': 190.0, 'Z': 0.00058387499999999933}, {'Y': 100.0, 'X': 100.0, 'Z': 0.00034499999999999982}, {'Y': 100.0, 'X': 10.0, 'Z': 0.00024037499999999927}, {'Y': 180.0, 'X': 10.0, 'Z': 0.0}, {'Y': 180.0, 'X': 100.0, 'Z': 0.00012487499999999999}, {'Y': 180.0, 'X': 190.0, 'Z': 0.00045737499999999945}]

points_with_reset = [{'Y': 20.0, 'X': 10.0, 'Z': 0.00073999999999999934}, {'Y': 20.0, 'X': 100.0, 'Z': 0.00046287499999999974}, {'Y': 20.0, 'X': 190.0, 'Z': 0.00046762499999999929}, {'Y': 100.0, 'X': 190.0, 'Z': 0.00060487499999999951}, {'Y': 100.0, 'X': 100.0, 'Z': 0.00035624999999999893}, {'Y': 100.0, 'X': 10.0, 'Z': 0.00026424999999999886}, {'Y': 180.0, 'X': 10.0, 'Z': 0.0}, {'Y': 180.0, 'X': 100.0, 'Z': 0.00012374999999999886}, {'Y': 180.0, 'X': 190.0, 'Z': 0.00046637499999999978}]

points = [{'Y': 0.0, 'X': 0.0, 'Z': 0.0}, {'Y': 0.0, 'X': 50.0, 'Z': -0.0007999999999999995}, {'Y': 50.0, 'X': 0.0, 'Z': -0.0010749999999999996}, {'Y': 0.0, 'X': -50.0, 'Z': -6.2500000000000056e-05}, {'Y': -50.0, 'X': 0.0, 'Z': 0.00017499999999999981}, {'Y': 0.0, 'X': 25.0, 'Z': -0.00028749999999999956}, {'Y': 25.0, 'X': 0.0, 'Z': -0.00038749999999999982}, {'Y': 0.0, 'X': -25.0, 'Z': 8.7499999999999904e-05}, {'Y': -25.0, 'X': 0.0, 'Z': 0.00017499999999999981}]
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x = []
y = []
z = []
for p in points:
    x.append(p["X"])
    y.append(p["Y"])
    z.append(p["Z"]*1000)

z2 = z

# Set up the canonical least squares form
degree = 2
Ax = np.vander(x, degree)
Ay = np.vander(y, degree)
A = np.hstack((Ax, Ay))
 
A = np.column_stack((np.ones(len(x)), x, y))

# Solve for a least squares estimate
(coeffs, residuals, rank, sing_vals) = np.linalg.lstsq(A, z)
 
X = np.linspace(min(x), max(x), 3)
Y = np.linspace(min(y), max(y), 3)
X, Y = np.meshgrid(X, Y)

Z = coeffs[0]+coeffs[1]*X + coeffs[2]*Y

ax.plot(x, y, z, linestyle="none", marker="o", mfc="none", markeredgecolor="red")

x = []
y = []
z = []
for p in points_with_reset:
    x.append(p["X"])
    y.append(p["Y"])
    z.append(p["Z"]*1000)

#ax.plot(x, y, z, linestyle="none", marker="o", mfc="none", markeredgecolor="green")
ax.plot_surface(X, Y, Z)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

#print "Diff Z: "+str(np.array(z2)-np.array(z))
plt.show()  


