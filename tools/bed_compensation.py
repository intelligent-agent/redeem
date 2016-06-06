"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random

# With reset of probe 
points = [{'Y': 0.0, 'X': 0.0, 'Z': 0.0}, {'Y': 0.0, 'X': 50.0, 'Z': -3.7500000000000207e-05}, {'Y': 50.0, 'X': 0.0, 'Z': 4.9999999999999697e-05}, {'Y': 0.0, 'X': -50.0, 'Z': -3.7500000000000207e-05}, {'Y': -40.0, 'X': 0.0, 'Z': 4.9999999999999697e-05}, {'Y': 0.0, 'X': 25.0, 'Z': 4.9999999999999697e-05}, {'Y': 25.0, 'X': 0.0, 'Z': 7.5000000000000414e-05}, {'Y': 0.0, 'X': -25.0, 'Z': 1.2500000000000358e-05}, {'Y': -25.0, 'X': 0.0, 'Z': 1.2500000000000358e-05}]

points = [{"Y": 0.05, "X": -0.05, "Z": 0.00048749999999999981}, {"Y": 0.05, "X": 0.05, "Z": 0.0}, {"Y": -0.05, "X": 0.0, "Z": 0.00021249999999999947}, {"Y": 0.025, "X": -0.025, "Z": 0.0013000000000000008}, {"Y": 0.025, "X": 0.025, "Z": 0.0010374999999999996}, {"Y": -0.025, "X": 0.0, "Z": 0.00088750000000000016}, {"Y": 0.0, "X": 0.0, "Z": 0.0015750000000000002}]


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x = []
y = []
z = []
for p in points:
    x.append(p["X"]*1000)
    y.append(p["Y"]*1000)
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
ax.plot_surface(X, Y, Z)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

#print "Diff Z: "+str(np.array(z2)-np.array(z))
plt.show()  


