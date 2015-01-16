# Jerk calculations

import numpy as np

jerk = 40

v1 = np.array([50, 0])
v2 = np.array([0, 50])

v = v2-v1
v_diff = np.sqrt(v[0]**2 + v[1]**2)

v1max = np.max(v1)
v2max = np.max(v2)
vx_1 = jerk/v_diff*v1max

print "V1: "+str(v1)
print "V2: "+str(v2)
print "V_diff: "+str(v_diff)
if v_diff > jerk:
    print "Corner can be printed at full speed"
print "vx_1: "+str(vx_1)

matrix_H = np.matrix('-0.5 0.5; -0.5 -0.5')
matrix_H_inv = np.linalg.inv(matrix_H)
v1h = np.array(np.dot(matrix_H_inv, v1))[0]
v2h = np.array(np.dot(matrix_H_inv, v2))[0]
vh = v2h-v1h
v_diff_h = np.sqrt(vh[0]**2 + vh[1]**2)

print "After H-bot transform:"
print "V1: "+str(v1h)
print "V2: "+str(v2h)
print "V_diff: "+str(v_diff_h)
if v_diff < jerk:
    print "Corner can be printed at full speed"
else:
    v1hmax = np.max(v1h)
    vxh_1 = (jerk/v_diff_h)*v1hmax
    v2hmax = np.max(v2h)
    vxh_2 = (jerk/v_diff_h)*v2hmax
    print "Corner speed must be reduced to "+str(vxh_1)+" and "+str(vxh_2)
