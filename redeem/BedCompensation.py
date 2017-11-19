"""
Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html


 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import copy 

class BedCompensation:

    @staticmethod
    def create_rotation_matrix(probe_points, probe_heights):
        probe_points = copy.deepcopy(probe_points)

        """ http://math.stackexchange.com/a/476311 """
        if len(probe_points) == 3:
            P0 = np.array([probe_points[0]["X"]/1000.0, probe_points[0]["Y"]/1000.0, probe_heights[0]/1000.0])
            P1 = np.array([probe_points[1]["X"]/1000.0, probe_points[1]["Y"]/1000.0, probe_heights[1]/1000.0])
            P2 = np.array([probe_points[2]["X"]/1000.0, probe_points[2]["Y"]/1000.0, probe_heights[2]/1000.0])
        else:
            # Add Z (height) to the probe points
            for k, v in enumerate(probe_points):
                probe_points[k]["X"] /= 1000.0
                probe_points[k]["Y"] /= 1000.0
                probe_points[k]["Z"] = probe_heights[k]/1000.0
            (P0, P1, P2) = BedCompensation.create_plane_from_points(probe_points)
        
        # calculate the bed normal vector
        P10 = BedCompensation.normalize(P0-P1)
        P21 = BedCompensation.normalize(P2-P1)
        bed_normal = BedCompensation.normalize(np.cross(P10, P21))

        # calculate a normal vector in world space in the same direction as the bed normal
        ideal_normal = np.array([0.0, 0.0, np.sign(bed_normal[2])])
        
        # calculate the rotation matrix that will align the ideal normal
        # with the bed normal
        v = np.cross(bed_normal, ideal_normal)
        c = np.dot(bed_normal, ideal_normal)
        s = np.linalg.norm(v)
        ssc = np.array([[0.0, -v[2], v[1]],
                        [v[2], 0.0, -v[0]],
                        [-v[1], v[0], 0.0]])
        
        R = np.eye(3) + ssc + (ssc**2)*(1.0 - c)/(s**2)
        
        # check if the rotation matrix is valid, if not then return identity matrix
        if np.all(np.isfinite(R)):
            return R 
            #TODO: This makes no sense, it should be R, not R/4
            return R*0.25 + np.eye(3)*0.75
        else:
            return np.eye(3)
        

    @staticmethod
    def normalize(vec):
        return vec/np.linalg.norm(vec)



    @staticmethod
    def create_plane_from_points(points):
        """ This method uses linear regression (least squares) to fit a plane 
        to a set of data points. This is useful if the number of probe points is > 3. 
        The plane is then used to sample three new points. """

        x = []
        y = []
        z = []
        for p in points:
            x.append(p["X"])
            y.append(p["Y"])
            z.append(p["Z"])

        A = np.column_stack((np.ones(len(x)), x, y))

        # Solve for a least squares estimate
        (coeffs, residuals, rank, sing_vals) = np.linalg.lstsq(A, z)
     
        X = np.linspace(min(x), max(x), 3)
        Y = np.linspace(min(y), max(y), 3)
        X, Y = np.meshgrid(X, Y)
        
        Z = coeffs[0]+coeffs[1]*X + coeffs[2]*Y

        # Resample the probe points based on the least squares plane found. 
        
        P0 = np.array([min(x), min(y), coeffs[0]+coeffs[1]*min(x)+coeffs[2]*min(y)])
        P1 = np.array([min(x), max(y), coeffs[0]+coeffs[1]*min(x)+coeffs[2]*max(y)])
        P2 = np.array([(max(x)-min(x))/2.0, max(y), coeffs[0]+coeffs[1]*(max(x)-min(x))/2.0+coeffs[2]*max(y)])

        return (P0, P1, P2)
        
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import json

    points = [{"Y": 0.0, "X": 65.0, "Z": -1.6499999999999995}, {"Y": 32.5, "X": 56.29, "Z": -1.0625}, {"Y": 56.29, "X": 32.5, "Z": -0.56249999999999967}, {"Y": 65.0, "X": 0.0, "Z": -0.40000000000000019}, {"Y": 56.29, "X": -32.5, "Z": -0.67500000000000027}, {"Y": 32.5, "X": -56.29, "Z": -1.1875000000000002}, {"Y": 0.0, "X": -65.0, "Z": -1.7499999999999998}, {"Y": -32.5, "X": -56.29, "Z": -2.1624999999999996}, {"Y": -56.29, "X": -32.5, "Z": -2.4250000000000003}, {"Y": -65.0, "X": -0.0, "Z": -2.4375000000000004}, {"Y": -56.29, "X": 32.5, "Z": -2.3374999999999995}, {"Y": -32.5, "X": 56.29, "Z": -2.0999999999999996}, {"Y": 0.0, "X": 32.5, "Z": -1.5624999999999996}, {"Y": 16.25, "X": 28.15, "Z": -1.2624999999999997}, {"Y": 28.15, "X": 16.25, "Z": -1.0375000000000003}, {"Y": 32.5, "X": 0.0, "Z": -0.9750000000000002}, {"Y": 28.15, "X": -16.25, "Z": -1.0874999999999999}, {"Y": 16.25, "X": -28.15, "Z": -1.3499999999999996}, {"Y": 0.0, "X": -32.5, "Z": -1.6624999999999999}, {"Y": -16.25, "X": -28.15, "Z": -1.9249999999999996}, {"Y": -28.15, "X": -16.25, "Z": -2.0625}, {"Y": -32.5, "X": -0.0, "Z": -2.087499999999999}, {"Y": -28.15, "X": 16.25, "Z": -2.0}, {"Y": -16.25, "X": 28.15, "Z": -1.8250000000000002}, {"Y": 0.0, "X": 0.0, "Z": -1.575}]
    fixed =  [{"Y": 0.0, "X": 65.0, "Z": -1.7000000000000002}, {"Y": 32.5, "X": 56.29, "Z": -1.6249999999999998}, {"Y": 56.29, "X": 32.5, "Z": -1.4749999999999996}, {"Y": 65.0, "X": 0.0, "Z": -1.425}, {"Y": 56.29, "X": -32.5, "Z": -1.5374999999999999}, {"Y": 32.5, "X": -56.29, "Z": -1.6375000000000002}, {"Y": 0.0, "X": -65.0, "Z": -1.6874999999999998}, {"Y": -32.5, "X": -56.29, "Z": -1.5624999999999996}, {"Y": -56.29, "X": -32.5, "Z": -1.4999999999999996}, {"Y": -65.0, "X": -0.0, "Z": -1.3749999999999996}, {"Y": -56.29, "X": 32.5, "Z": -1.45}, {"Y": -32.5, "X": 56.29, "Z": -1.6249999999999998}, {"Y": 0.0, "X": 32.5, "Z": -1.575}, {"Y": 16.25, "X": 28.15, "Z": -1.5249999999999995}, {"Y": 28.15, "X": 16.25, "Z": -1.4749999999999996}, {"Y": 32.5, "X": 0.0, "Z": -1.45}, {"Y": 28.15, "X": -16.25, "Z": -1.4749999999999996}, {"Y": 16.25, "X": -28.15, "Z": -1.5374999999999999}, {"Y": 0.0, "X": -32.5, "Z": -1.5874999999999995}, {"Y": -16.25, "X": -28.15, "Z": -1.5999999999999999}, {"Y": -28.15, "X": -16.25, "Z": -1.575}, {"Y": -32.5, "X": -0.0, "Z": -1.5500000000000003}, {"Y": -28.15, "X": 16.25, "Z": -1.5374999999999999}, {"Y": -16.25, "X": 28.15, "Z": -1.5624999999999996}, {"Y": 0.0, "X": 0.0, "Z": -1.5500000000000003}]

    add = points[-1]["Z"]

    x1, y1, z1 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], d['Z']])), points)))
    x3, y3, z3 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], d['Z']])), fixed)))

    z = map(lambda d: d['Z'], points)
    Rn = BedCompensation.create_rotation_matrix(points, z)
    
    x2, y2, z2 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], add  ]).dot(Rn)), points )))


    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x1, y1, z1, linestyle="none", marker="o", mfc="none", markeredgecolor="red")
    ax.plot(x2, y2, z2, linestyle="none", marker=".", mfc="none", markeredgecolor="green")
    ax.plot(x3, y3, z3, linestyle="none", marker="o", mfc="none", markeredgecolor="blue")

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    print("Level bed max diff before: "+str(max(z1)-min(z1))+" after: "+str(max(z3)-min(z3)))

    print("var matrix = "+json.dumps(Rn.tolist())+";")
    probe = {"x": x1, "y": y1, "z": z1}
    print("var probe = "+json.dumps(probe)+";")
    fixed = {"x": x3, "y": y3, "z": z3}
    print("var fixed = "+json.dumps(fixed)+";")

    plt.show()
    

