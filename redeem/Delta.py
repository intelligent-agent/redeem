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


class Delta:
    Hez = 0.0601    # Distance head extends below the effector.
    L   = 0.322     # Length of the rod
    r   = 0.175    # Radius of the columns
    Ae  = 0.02032  # Effector offset
    Be  = 0.02032
    Ce  = 0.02032

    # Hijacking carriage offset to become carraige offset error.

    Aco = 0.00
    Bco = 0.00
    Cco = 0.00

    # Compensation for positional error on the columns
    # https://github.com/hercek/Marlin/blob/Marlin_v1/calibration.wxm
    Apxe = 0.00
    Apye = 0.00
    Bpxe = 0.00
    Bpye = 0.00
    Cpxe = 0.00
    Cpye = 0.00

    @staticmethod
    def recalculate():
    
        # Column theta
        At = np.pi / 2.0
        Bt = 7.0 * np.pi / 6.0
        Ct = 11.0 * np.pi / 6.0

        # Calculate the column positions 
        Apx = (Delta.Aco + Delta.r)*np.cos(At) + Delta.Apxe
        Apy = (Delta.Aco + Delta.r)*np.sin(At) + Delta.Apye
        Bpx = (Delta.Bco + Delta.r)*np.cos(Bt) + Delta.Bpxe
        Bpy = (Delta.Bco + Delta.r)*np.sin(Bt) + Delta.Bpye
        Cpx = (Delta.Cco + Delta.r)*np.cos(Ct) + Delta.Cpxe
        Cpy = (Delta.Cco + Delta.r)*np.sin(Ct) + Delta.Cpye

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

        logging.info("Delta calibration calculated. Current settings:")
        logging.info("Column A(X): Acoe="+str(Delta.Aco)+" Apxe="+str(Delta.Apxe)+" Apye="+str(Delta.Apye))
        logging.info("Column B(X): Bcoe="+str(Delta.Bco)+" Bpxe="+str(Delta.Bpxe)+" Bpye="+str(Delta.Bpye))
        logging.info("Column C(X): Ccoe="+str(Delta.Cco)+" Cpxe="+str(Delta.Cpxe)+" Cpye="+str(Delta.Cpye))
        logging.info("Radius (r) ="+str(Delta.r)+" Rod Length (L)="+str(Delta.L))

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
