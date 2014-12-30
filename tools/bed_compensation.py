"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random

# With reset of probe 
points = [{'Y': 20.0, 'X': 10.0, 'Z': 0.00072549999999999958}, {'Y': 20.0, 'X': 100.0, 'Z': 0.00040387499999999972}, {'Y': 20.0, 'X': 190.0, 'Z': 0.00049262500000000001}, {'Y': 100.0, 'X': 190.0, 'Z': 0.00059549999999999968}, {'Y': 100.0, 'X': 100.0, 'Z': 0.00034949999999999998}, {'Y': 100.0, 'X': 10.0, 'Z': 0.00024949999999999972}, {'Y': 180.0, 'X': 10.0, 'Z': 0.0}, {'Y': 180.0, 'X': 100.0, 'Z': 0.00016087499999999956}, {'Y': 180.0, 'X': 190.0, 'Z': 0.00048962499999999961}]

points =  [{'Y': 20.0, 'X': 10.0, 'Z': 0.0007356249999999993}, {'Y': 20.0, 'X': 100.0, 'Z': 0.00046424999999999939}, {'Y': 20.0, 'X': 190.0, 'Z': 0.00056949999999999969}, {'Y': 100.0, 'X': 190.0, 'Z': 0.00066149999999999976}, {'Y': 100.0, 'X': 100.0, 'Z': 0.00040599999999999924}, {'Y': 100.0, 'X': 10.0, 'Z': 0.00027874999999999948}, {'Y': 180.0, 'X': 10.0, 'Z': 0.0}, {'Y': 180.0, 'X': 100.0, 'Z': 0.00015949999999999992}, {'Y': 180.0, 'X': 190.0, 'Z': 0.00049924999999999969}]

points = [{'Y': 20.0, 'X': 10.0, 'Z': 0.00073999999999999934}, {'Y': 20.0, 'X': 100.0, 'Z': 0.00046287499999999974}, {'Y': 20.0, 'X': 190.0, 'Z': 0.00046762499999999929}, {'Y': 100.0, 'X': 190.0, 'Z': 0.00060487499999999951}, {'Y': 100.0, 'X': 100.0, 'Z': 0.00035624999999999893}, {'Y': 100.0, 'X': 10.0, 'Z': 0.00026424999999999886}, {'Y': 180.0, 'X': 10.0, 'Z': 0.0}, {'Y': 180.0, 'X': 100.0, 'Z': 0.00012374999999999886}, {'Y': 180.0, 'X': 190.0, 'Z': 0.00046637499999999978}]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x = []
y = []
z = []
for p in points:
    x.append(p["X"])
    y.append(p["Y"])
    z.append(p["Z"]*1000)

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
ax.plot_surface(X, Y, Z)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()
