import matplotlib.pyplot as plt
import numpy as np

import sys, os
lib_path = os.path.abspath('../software')
sys.path.append(lib_path)

from Path import Path

t = np.arange(0, 3*np.pi/2+(np.pi/10), np.pi/10)
speed = 0.3
paths = []
for i in t:
    paths.append(Path({"X": np.sin(i), "Y": np.cos(i)}, speed, Path.ABSOLUTE))
paths.append(Path({"X": 0.0, "Y": 0.0}, speed, Path.ABSOLUTE))

x = [0]
y = [0]
prev = None
for path in paths:
    path.set_prev(prev)
    prev = path
    x.append(path.end_pos[0]) 
    y.append(path.end_pos[1])

plt.plot(x, y)
plt.show()
