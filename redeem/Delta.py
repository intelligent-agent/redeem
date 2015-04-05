"""
Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 This work in this file has been heavily influenced by the work of Steve Graves
 from his document on Delta printer kinematics: https://groups.google.com/forum/#!topic/deltabot/V6ATBdT43eU

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
import logging
import math

class Delta:
    Hez = 0.0601    # Distance head extends below the effector.
    L   = 0.322     # Length of the rod
    r   = 0.175    # Radius of the columns
    Ae  = 0.02032  # Effector offset
    Be  = 0.02032
    Ce  = 0.02032

    A_radial = 0.00            # Radius error of the named column                          
    B_radial = 0.00                                                                      
    C_radial = 0.00                                                                     
    A_tangential = 0.00                                                                 
    B_tangential = 0.00                                                                
    C_tangential = 0.00


    @staticmethod
    def recalculate():
    
        # Column theta
        At = np.pi / 2.0
        Bt = 7.0 * np.pi / 6.0
        Ct = 11.0 * np.pi / 6.0

        # Calculate the column tangential offsets
        Apxe = Delta.A_tangential   # Tower A doesn't require a separate y component
        Apye = 0.00
        Bpxe = Delta.B_tangential/2
        Bpye = np.sqrt(3)*(-Delta.B_tangential/2)
        Cpxe = np.sqrt(3)*(Delta.C_tangential/2)
        Cpye = Delta.C_tangential/2

        # Calculate the column positions 
        Apx = (Delta.A_radial + Delta.r)*np.cos(At) + Apxe
        Apy = (Delta.A_radial + Delta.r)*np.sin(At) + Apye
        Bpx = (Delta.B_radial + Delta.r)*np.cos(Bt) + Bpxe
        Bpy = (Delta.B_radial + Delta.r)*np.sin(Bt) + Bpye
        Cpx = (Delta.C_radial + Delta.r)*np.cos(Ct) + Cpxe
        Cpy = (Delta.C_radial + Delta.r)*np.sin(Ct) + Cpye

        # Calculate the effector positions
        Aex = Delta.Ae*np.cos(At)
        Aey = Delta.Ae*np.sin(At)
        Bex = Delta.Be*np.cos(Bt)
        Bey = Delta.Be*np.sin(Bt)
        Cex = Delta.Ce*np.cos(Ct)
        Cey = Delta.Ce*np.sin(Ct)

        # Calculate the virtual column positions
        Delta.Avx = Apx - Aex
        Delta.Avy = Apy - Aey
        Delta.Bvx = Bpx - Bex
        Delta.Bvy = Bpy - Bey
        Delta.Cvx = Cpx - Cex
        Delta.Cvy = Cpy - Cey

        Delta.p1 = np.array([Delta.Avx, Delta.Avy, 0])
        Delta.p2 = np.array([Delta.Bvx, Delta.Bvy, 0])
        Delta.p3 = np.array([Delta.Cvx, Delta.Cvy, 0])


        logging.info("Delta calibration calculated. Current settings:")
        logging.info("Column A(X): A_radial={:3.5}mm A_tangential={:3.5}mm".format( Delta.A_radial*1000.0, Delta.A_tangential*1000.0))
        logging.info("Column B(Y): B_radial={:3.5}mm B_tangential={:3.5}mm".format( Delta.B_radial*1000.0, Delta.B_tangential*1000.0))
        logging.info("Column C(Z): C_radial={:3.5}mm C_tangential={:3.5}mm".format( Delta.C_radial*1000.0, Delta.C_tangential*1000.0))
        logging.info("Radius (r) = {:3.5}mm  Rod Length (L)= {:3.5}mm".format(Delta.r*1000.0, Delta.L*1000.0))



    @staticmethod
    def inverse_kinematics(X, Y, Z):
        """
        Inverse kinematics for Delta bot. Returns position for column
        A, B, and C
         """

        # Calculate the translation in carriage position
        Acz = np.sqrt(Delta.L**2 - (X - Delta.Avx)**2 - (Y - Delta.Avy)**2)
        Bcz = np.sqrt(Delta.L**2 - (X - Delta.Bvx)**2 - (Y - Delta.Bvy)**2)
        Ccz = np.sqrt(Delta.L**2 - (X - Delta.Cvx)**2 - (Y - Delta.Cvy)**2)

        # Calculate the position of the carriages
        Az = Z + Acz + Delta.Hez
        Bz = Z + Bcz + Delta.Hez
        Cz = Z + Ccz + Delta.Hez
        
        return np.array([Az, Bz, Cz])

    @staticmethod
    def inverse_kinematics2(X, Y, Z):
        """
        Inverse kinematics for Delta bot. Returns position for column
        A, B, and C
         """

        # Calculate the translation in carriage position
        Acz = math.sqrt(Delta.L**2 - (X - Delta.Avx)**2 - (Y - Delta.Avy)**2)
        Bcz = math.sqrt(Delta.L**2 - (X - Delta.Bvx)**2 - (Y - Delta.Bvy)**2)
        Ccz = math.sqrt(Delta.L**2 - (X - Delta.Cvx)**2 - (Y - Delta.Cvy)**2)

        # Calculate the position of the carriages
        Az = Z + Acz + Delta.Hez
        Bz = Z + Bcz + Delta.Hez
        Cz = Z + Ccz + Delta.Hez

        return np.array([Az, Bz, Cz])

    @staticmethod
    def forward_kinematics(Az, Bz, Cz):
        """
        Forward kinematics for Delta Bot. Returns the X, Y, Z point given
        column translations
        """
        p1 = np.array([Delta.Avx, Delta.Avy, Az])
        p2 = np.array([Delta.Bvx, Delta.Bvy, Bz])
        p3 = np.array([Delta.Cvx, Delta.Cvy, Cz])

        p12 = p2 - p1

        ex = p12 / np.linalg.norm(p12)
        p13 = p3 - p1
        i = np.dot(ex, p13)
        iex = i * ex
        ey = (p13 - iex) / np.linalg.norm(p13 - iex)
        ez = np.cross(ex, ey)

        d = np.linalg.norm(p12)

        j = np.dot(ey, p13)  # Signed magnitude of the Y component

        D = Delta.L

        x = d / 2
        y = ((i ** 2 + j ** 2) / 2 - i * x) / j
        z = np.sqrt(D ** 2 - x ** 2 - y ** 2)

        # Construct the final point
        XYZ = p1 + x*ex + y*ey + -z*ez

        return XYZ

    @staticmethod
    def forward_kinematics2(Az, Bz, Cz):
        """
        Forward kinematics for Delta Bot. Returns the X, Y, Z point given
        column translations
        """
        Delta.p1[2] = Az
        Delta.p2[2] = Bz
        Delta.p3[2] = Cz
        p1 = Delta.p1
        p2 = Delta.p2
        p3 = Delta.p3

        p12 = p2 - p1

        ex = p12 / Delta.norm(p12)
        p13 = p3 - p1
        i = np.dot(ex, p13)
        iex = i * ex
        p13iex = p13 - iex
        ey = (p13iex) / Delta.norm(p13iex)
        ez = Delta.cross(ex, ey)

        d = Delta.norm(p12)

        j = Delta.dot(ey, p13)  # Signed magnitude of the Y component

        D = Delta.L

        x = d / 2
        y = ((i ** 2 + j ** 2) / 2 - i * x) / j
        z = math.sqrt(D ** 2 - x ** 2 - y ** 2)

        # Construct the final point
        XYZ = p1 + x*ex + y*ey + -z*ez

        return XYZ
        
    @staticmethod
    def vertical_offset(Az, Bz, Cz):
        """
        vertical offset between circumcenter of carriages and the effector
        """
        Delta.p1[2] = Az
        Delta.p2[2] = Bz
        Delta.p3[2] = Cz
        
        # location of virtual carriages
        p1 = Delta.p1
        p2 = Delta.p2
        p3 = Delta.p3
        
        # normal to the plane
        plane_normal = Delta.cross(p1-p2,p2-p3)
        plane_normal_length = Delta.norm(plane_normal)
        plane_normal /= plane_normal_length
        
        # radius of circle
        r = (Delta.norm(p1-p2)*Delta.norm(p2-p3)*Delta.norm(p3-p1))/(2*plane_normal_length)

        # distance below the plane
        offset = plane_normal*math.sqrt(Delta.L**2 - r**2)
        
        return offset[2]

    @staticmethod
    def norm(p):
        return math.sqrt(p[0]**2+p[1]**2+p[2]**2)

    @staticmethod
    def cross(a, b):
        c = np.array([a[1]*b[2] - a[2]*b[1],
             a[2]*b[0] - a[0]*b[2],
             a[0]*b[1] - a[1]*b[0]])
        return c

    @staticmethod
    def dot(a, b):
        return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "timeit":
            import timeit
            print timeit.timeit('Delta.inverse_kinematics(0.1, 0.1, 0.1)', number=1000, setup='from Delta import Delta; Delta.recalculate()')
            print timeit.timeit('Delta.inverse_kinematics2(0.1, 0.1, 0.1)', number=1000, setup='from Delta import Delta; Delta.recalculate()')
            print timeit.timeit('Delta.forward_kinematics(0.1, 0.1, 0.1)', number=1000, setup='from Delta import Delta; Delta.recalculate()')
            print timeit.timeit('Delta.forward_kinematics2(0.1, 0.1, 0.1)', number=1000, setup='from Delta import Delta; Delta.recalculate()')


        elif sys.argv[1] == "yappi":
            import yappi
            Delta.recalculate()
            yappi.start()
            for i in xrange(100):
                Delta.forward_kinematics(0.1, 0.1, 0.1)
            for i in xrange(100):
                Delta.forward_kinematics2(0.1, 0.1, 0.1)
            yappi.get_func_stats().print_all()
    else:
        Delta.recalculate()
        print Delta.inverse_kinematics(0.1, 0.1, 0.1)
        print Delta.inverse_kinematics2(0.1, 0.1, 0.1)
        print Delta.forward_kinematics(0.1, 0.1, 0.1)
        print Delta.forward_kinematics2(0.1, 0.1, 0.1)
