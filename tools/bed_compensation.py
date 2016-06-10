"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random

single = True

# With reset of probe 
before = [{"Y": 0.0, "X": 0.072, "Z": 0.0}, {"Y": 0.06848, "X": 0.02225, "Z": 0.0017124999999999998}, {"Y": 0.04232, "X": -0.05825, "Z": 0.0023875000000000003}, {"Y": -0.04232, "X": -0.05825, "Z": 0.0017499999999999998}, {"Y": -0.06848, "X": 0.02225, "Z": 0.00025000000000000001}, {"Y": 0.0, "X": 0.048, "Z": 0.00028749999999999967}, {"Y": 0.045649999999999996, "X": 0.01483, "Z": 0.0014999999999999998}, {"Y": 0.028210000000000002, "X": -0.038829999999999996, "Z": 0.002075}, {"Y": -0.028210000000000002, "X": -0.038829999999999996, "Z": 0.0014750000000000002}, {"Y": -0.045649999999999996, "X": 0.01483, "Z": 0.00042499999999999981}, {"Y": 0.0, "X": 0.024, "Z": 0.00072499999999999962}, {"Y": 0.02283, "X": 0.0074199999999999995, "Z": 0.0013125000000000001}, {"Y": 0.01411, "X": -0.019420000000000003, "Z": 0.0016624999999999999}, {"Y": -0.01411, "X": -0.019420000000000003, "Z": 0.0012999999999999999}, {"Y": -0.02283, "X": 0.0074199999999999995, "Z": 0.00076250000000000016}, {"Y": 0.0, "X": 0.0, "Z": 0.0011374999999999998}]
after  = [{"Y": 0.0, "X": 0.072, "Z": 0.0}, {"Y": 0.06848, "X": 0.02225, "Z": 0.00062500000000000001}, {"Y": 0.04232, "X": -0.05825, "Z": 0.0017000000000000001}, {"Y": -0.04232, "X": -0.05825, "Z": 0.0024625000000000003}, {"Y": -0.06848, "X": 0.02225, "Z": 0.0014125000000000001}, {"Y": 0.0, "X": 0.048, "Z": 0.00041250000000000011}, {"Y": 0.045649999999999996, "X": 0.01483, "Z": 0.00090000000000000041}, {"Y": 0.028210000000000002, "X": -0.038829999999999996, "Z": 0.0017500000000000003}, {"Y": -0.028210000000000002, "X": -0.038829999999999996, "Z": 0.0021000000000000003}, {"Y": -0.045649999999999996, "X": 0.01483, "Z": 0.0014125000000000001}, {"Y": 0.0, "X": 0.024, "Z": 0.00098750000000000031}, {"Y": 0.02283, "X": 0.0074199999999999995, "Z": 0.0012250000000000002}, {"Y": 0.01411, "X": -0.019420000000000003, "Z": 0.0017125}, {"Y": -0.01411, "X": -0.019420000000000003, "Z": 0.0018250000000000002}, {"Y": -0.02283, "X": 0.0074199999999999995, "Z": 0.0014500000000000001}, {"Y": 0.0, "X": 0.0, "Z": 0.0015000000000000002}]


x1, y1, z1 = map(list, zip(*map(lambda d: (d['X']*1000, d['Y']*1000, d['Z']*1000) , before)))
x2, y2, z2 = map(list, zip(*map(lambda d: (d['X']*1000, d['Y']*1000, d['Z']*1000) , after )))



fig = plt.figure()
if single:
    ax = fig.add_subplot(111, projection='3d')
else:
    ax = fig.add_subplot(211, projection='3d')
    
(x, y, z) = (x1, y1, z1)
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

ax.plot(x1, y1, z1, linestyle="none", marker="o", mfc="none", markeredgecolor="red")
if single:
    ax.plot(x2, y2, z2, linestyle="none", marker="o", mfc="none", markeredgecolor="green")
ax.plot_surface(X, Y, Z)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

if not single:

    ax = fig.add_subplot(212, projection='3d')
    (x, y, z) = (x2, y2, z2)
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

    ax.plot_surface(X, Y, Z)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')



print "Before delta: "+str(max(z1)-min(z1))
print "After  delta: "+str(max(z2)-min(z2))

plt.show()  


