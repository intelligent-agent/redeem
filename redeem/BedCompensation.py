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
            #return R 
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
    from Path import AbsolutePath, G92Path

    points = [{"Y": 0.0, "X": 70.0, "Z": -7.7999999999999998}, {"Y": 35.0, "X": 60.62, "Z": -7.2999999999999998}, {"Y": 60.62, "X": 35.0, "Z": -6.5874999999999995}, {"Y": 70.0, "X": 0.0, "Z": -5.8125}, {"Y": 60.62, "X": -35.0, "Z": -5.4249999999999998}, {"Y": 35.0, "X": -60.62, "Z": -5.25}, {"Y": 0.0, "X": -70.0, "Z": -5.3125}, {"Y": -35.0, "X": -60.62, "Z": -5.5125000000000002}, {"Y": -60.62, "X": -35.0, "Z": -5.9625000000000004}, {"Y": -70.0, "X": -0.0, "Z": -6.6375000000000002}, {"Y": -60.62, "X": 35.0, "Z": -7.5249999999999995}, {"Y": -35.0, "X": 60.62, "Z": -7.9500000000000002}, {"Y": 0.0, "X": 46.67, "Z": -7.3624999999999998}, {"Y": 23.33, "X": 40.41, "Z": -6.9625000000000004}, {"Y": 40.41, "X": 23.33, "Z": -6.4749999999999996}, {"Y": 46.67, "X": 0.0, "Z": -6.0}, {"Y": 40.41, "X": -23.33, "Z": -5.6624999999999996}, {"Y": 23.33, "X": -40.41, "Z": -5.5374999999999996}, {"Y": 0.0, "X": -46.67, "Z": -5.6624999999999996}, {"Y": -23.33, "X": -40.41, "Z": -5.8875000000000002}, {"Y": -40.41, "X": -23.33, "Z": -6.3125}, {"Y": -46.67, "X": -0.0, "Z": -6.7375000000000007}, {"Y": -40.41, "X": 23.33, "Z": -7.2125000000000004}, {"Y": -23.33, "X": 40.41, "Z": -7.4749999999999996}, {"Y": 0.0, "X": 23.33, "Z": -6.8374999999999995}, {"Y": 11.67, "X": 20.21, "Z": -6.6624999999999996}, {"Y": 20.21, "X": 11.67, "Z": -6.4124999999999996}, {"Y": 23.33, "X": 0.0, "Z": -6.1749999999999998}, {"Y": 20.21, "X": -11.67, "Z": -6.0124999999999993}, {"Y": 11.67, "X": -20.21, "Z": -5.9500000000000002}, {"Y": 0.0, "X": -23.33, "Z": -6.0250000000000004}, {"Y": -11.67, "X": -20.21, "Z": -6.1624999999999996}, {"Y": -20.21, "X": -11.67, "Z": -6.4000000000000004}, {"Y": -23.33, "X": -0.0, "Z": -6.6375000000000002}, {"Y": -20.21, "X": 11.67, "Z": -6.8250000000000002}, {"Y": -11.67, "X": 20.21, "Z": -6.9375}, {"Y": 0.0, "X": 0.0, "Z": -6.4124999999999996}]
    fixed =  [{"Y": 0.0, "X": 70.0, "Z": -6.5625}, {"Y": 35.0, "X": 60.62, "Z": -6.5}, {"Y": 60.62, "X": 35.0, "Z": -6.375}, {"Y": 70.0, "X": 0.0, "Z": -6.1749999999999998}, {"Y": 60.62, "X": -35.0, "Z": -6.25}, {"Y": 35.0, "X": -60.62, "Z": -6.3125}, {"Y": 0.0, "X": -70.0, "Z": -6.3875000000000002}, {"Y": -35.0, "X": -60.62, "Z": -6.2750000000000004}, {"Y": -60.62, "X": -35.0, "Z": -6.1749999999999998}, {"Y": -70.0, "X": -0.0, "Z": -6.1875}, {"Y": -60.62, "X": 35.0, "Z": -6.4625000000000004}, {"Y": -35.0, "X": 60.62, "Z": -6.6375000000000002}, {"Y": 0.0, "X": 46.67, "Z": -6.4500000000000002}, {"Y": 23.33, "X": 40.41, "Z": -6.3375000000000004}, {"Y": 40.41, "X": 23.33, "Z": -6.2625000000000002}, {"Y": 46.67, "X": 0.0, "Z": -6.2249999999999996}, {"Y": 40.41, "X": -23.33, "Z": -6.2374999999999998}, {"Y": 23.33, "X": -40.41, "Z": -6.2874999999999996}, {"Y": 0.0, "X": -46.67, "Z": -6.3624999999999998}, {"Y": -23.33, "X": -40.41, "Z": -6.4000000000000004}, {"Y": -40.41, "X": -23.33, "Z": -6.4000000000000004}, {"Y": -46.67, "X": -0.0, "Z": -6.3624999999999998}, {"Y": -40.41, "X": 23.33, "Z": -6.4749999999999996}, {"Y": -23.33, "X": 40.41, "Z": -6.5250000000000004}, {"Y": 0.0, "X": 23.33, "Z": -6.3375000000000004}, {"Y": 11.67, "X": 20.21, "Z": -6.2999999999999998}, {"Y": 20.21, "X": 11.67, "Z": -6.2625000000000002}, {"Y": 23.33, "X": 0.0, "Z": -6.25}, {"Y": 20.21, "X": -11.67, "Z": -6.2750000000000004}, {"Y": 11.67, "X": -20.21, "Z": -6.2874999999999996}, {"Y": 0.0, "X": -23.33, "Z": -6.3499999999999996}, {"Y": -11.67, "X": -20.21, "Z": -6.375}, {"Y": -20.21, "X": -11.67, "Z": -6.375}, {"Y": -23.33, "X": -0.0, "Z": -6.3875000000000002}, {"Y": -20.21, "X": 11.67, "Z": -6.4000000000000004}, {"Y": -11.67, "X": 20.21, "Z": -6.4000000000000004}, {"Y": 0.0, "X": 0.0, "Z": -6.3250000000000002}]

    R = np.array(   [[1.0, 0.0, -0.004555437397842705], [0.0, 1.0, 0.0017681084085466128], [0.0046400016993029996, -0.001755690048614332, 1.0]]	 )
    print "Current rotation matrix: \n"+str(R)    

    add = points[-1]["Z"]


    x1, y1, z1 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], d['Z']])), points)))
    x2, y2, z2 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], add  ]).dot(R)), points )))
    x3, y3, z3 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], d['Z']])), fixed)))

    x4, y4, z4 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], d['Z']])), points)))
    Rn = BedCompensation.create_rotation_matrix(points, z4)
    x4, y4, z4 = map(list, zip(*map(lambda d: tuple(np.array([d['X'], d['Y'], add  ]).dot(Rn)), points )))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x1, y1, z1, linestyle="none", marker="o", mfc="none", markeredgecolor="red")
    ax.plot(x2, y2, z2, linestyle="none", marker=".", mfc="none", markeredgecolor="green")
    ax.plot(x4, y4, z4, linestyle="none", marker="*", mfc="none", markeredgecolor="orange")
    ax.plot(x3, y3, z3, linestyle="none", marker="o", mfc="none", markeredgecolor="blue")

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')


    plt.show()
    

