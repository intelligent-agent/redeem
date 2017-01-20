/*
  This file is part of Redeem - 3D Printer control software

  Author: Elias Bakken
  email: elias(at)iagent(dot)no
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

*/

#include "Delta.h"

#define _USE_MATH_DEFINES
#include <math.h>

Delta::Delta()
{
  Hez = 0.0;
  L = 0.0;
  r = 0.0;
	
  A_radial = 0.0;                   
  B_radial = 0.0;                                                                      
  C_radial = 0.0;  
                                                                     
  A_angular = 0.0;                                                                 
  B_angular = 0.0;                                                                
  C_angular = 0.0;

  recalculate();
}

Delta::~Delta() {}

void Delta::setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in)
{
  Hez = Hez_in;
  L = L_in;
  r = r_in;

  recalculate();
}
  
void Delta::setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in)
{
  A_radial = A_radial_in;                   
  B_radial = B_radial_in;                                                                      
  C_radial = C_radial_in; 

  recalculate();
}
void Delta::setAngularError(FLOAT_T A_angular_in, FLOAT_T B_angular_in, FLOAT_T C_angular_in)
{
  A_angular = A_angular_in;
  B_angular = B_angular_in;
  C_angular = C_angular_in;

  recalculate();
}

FLOAT_T degreesToRadians(FLOAT_T degrees)
{
  return degrees * M_PI / 180.0;
}

void Delta::recalculate(void)
{
  // Column theta
  const FLOAT_T At = degreesToRadians(90.0 + A_angular);
  const FLOAT_T Bt = degreesToRadians(210.0 + B_angular);
  const FLOAT_T Ct = degreesToRadians(330.0 + C_angular);

  // Calculate the column positions 
  Avx = (A_radial + r)*cos(At);
  Avy = (A_radial + r)*sin(At);
  Bvx = (B_radial + r)*cos(Bt);
  Bvy = (B_radial + r)*sin(Bt);
  Cvx = (C_radial + r)*cos(Ct);
  Cvy = (C_radial + r)*sin(Ct);
  
  //~ LOG("Delta: Avx = " << Avx << ", Avy = " << Avy << "\n");
  //~ LOG("Delta: Bvx = " << Bvx << ", Bvy = " << Bvy << "\n");
  //~ LOG("Delta: Cvx = " << Cvx << ", Cvy = " << Cvy << "\n");

}

void Delta::worldToDelta(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz)
{
  /*
    Inverse kinematics for Delta bot. Returns position for column
    A, B, and C
  */
    
  FLOAT_T L2 = L*L;
    
  FLOAT_T XA = X - Avx;
  FLOAT_T XB = X - Bvx;
  FLOAT_T XC = X - Cvx;
    
  FLOAT_T YA = Y - Avy;
  FLOAT_T YB = Y - Bvy;
  FLOAT_T YC = Y - Cvy;

  // Calculate the translation in carriage position
  FLOAT_T Acz = sqrt(L2 - XA*XA - YA*YA);
  FLOAT_T Bcz = sqrt(L2 - XB*XB - YB*YB);
  FLOAT_T Ccz = sqrt(L2 - XC*XC - YC*YC);

  // Calculate the position of the carriages
  *Az = Z + Acz + Hez;
  *Bz = Z + Bcz + Hez;
  *Cz = Z + Ccz + Hez;
  
  //~ LOG("Delta: Az = " << *Az << "\n");
  //~ LOG("Delta: Bz = " << *Bz << "\n");
  //~ LOG("Delta: Cz = " << *Cz << "\n");
	
  return;
}

void Delta::deltaToWorld(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z)
{
  /* Forward kinematics for Delta Bot. Calculates the X, Y, Z point given
     column translations
  */

  Vector3 p1 = Vector3(Avx, Avy, Az);
  Vector3 p2 = Vector3(Bvx, Bvy, Bz);
  Vector3 p3 = Vector3(Cvx, Cvy, Cz);

  Vector3 p12 = p2 - p1;
  Vector3 p13 = p3 - p1;
    
  FLOAT_T d = vabs(p12);
    
  Vector3 ex = p12/d;
    
  FLOAT_T i = dot(ex, p13);
  Vector3 iex = i*ex;
    
    
  Vector3 ey = (p13 - iex) / vabs(p13 - iex);
  Vector3 ez = cross(ex, ey);
    
  FLOAT_T j = dot(ey, p13);
    
  FLOAT_T x = d/2.0;
  FLOAT_T y = ((i*i + j*j)/2.0 - i*x)/j;
  FLOAT_T z = sqrt(L*L - x*x - y*y);
    
  Vector3 effector = p1 + x*ex + y*ey - z*ez;
    
  *X = effector.x;
  *Y = effector.y;
  *Z = effector.z;
  
  //~ LOG("Delta: X = " << *X << "\n");
  //~ LOG("Delta: Y = " << *Y << "\n");
  //~ LOG("Delta: Z = " << *Z << "\n");
	
  return;
}


void Delta::verticalOffset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset)
{
  // vertical offset between circumcenter of carriages and the effector

  Vector3 p1 = Vector3(Avx, Avy, Az);
  Vector3 p2 = Vector3(Bvx, Bvy, Bz);
  Vector3 p3 = Vector3(Cvx, Cvy, Cz);
  
  // normal to the plane
  Vector3 plane_normal = cross(p1 - p2, p2 - p3);
  FLOAT_T plane_normal_length = vabs(plane_normal);
  plane_normal /= plane_normal_length;
  
  // radius of circle
  FLOAT_T r = (vabs(p1 - p2)*vabs(p2 - p3)*vabs(p3 - p1)) / (2 * plane_normal_length);
  
  // distance below the plane
  *offset = plane_normal.z*sqrt(L*L - r*r);
  
  return;
}
