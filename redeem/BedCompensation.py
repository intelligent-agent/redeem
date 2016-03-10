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






# Helper functions for kinematics for Delta printers
import numpy as np  # Needed for sqrt

class BedCompensation:

    @staticmethod
    def create_rotation_matrix(probe_points, probe_heights):
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
        v = np.cross(ideal_normal, bed_normal)
        ssc = np.array([[0.0, -v[2], v[1]],
                        [v[2], 0.0, -v[0]],
                        [-v[1], v[0], 0.0]])
        
        R = np.eye(3) + ssc + ssc**2*(1.0 - np.dot(ideal_normal, bed_normal))/(np.linalg.norm(v)**2)
        
        return R

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
    probe_points = [{'Y': 100.0, 'X': 0.0, 'Z': 0}, 
                    {'Y': -50.0, 'X': -86.6, 'Z': 0}, 
                    {'Y': -50.0, 'X': 86.6, 'Z': 0}]
    probe_heights = [-10.0, 0.0, 0.0]
    
    R = BedCompensation.create_rotation_matrix(probe_points, probe_heights)
    
    test_point_0 = np.array([0.0, 0.0, 1.0])
    
    print np.dot(R, test_point_0)

    

