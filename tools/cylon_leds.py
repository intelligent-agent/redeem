"""
This script allows plotting the surface of the bed. 
"""

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random


x = np.linspace(0.0, 6.28, 100)
y = (0.5+0.5*np.sin(x+0.0*np.pi/2.0))
z = (0.5+0.5*np.sin(x+0.0*np.pi/2.0))**1.9


fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(x, y, x, z)

plt.show()  


