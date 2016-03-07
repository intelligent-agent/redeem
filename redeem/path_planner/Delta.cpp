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

Delta::Delta()
{
  Hez = 0.0;
  L = 0.0;
  r = 0.0;
	
  Ae = 0.0;
  Be = 0.0;
  Ce = 0.0;
	
  A_radial = 0.0;                   
  B_radial = 0.0;                                                                      
  C_radial = 0.0;  
                                                                     
  A_tangential = 0.0;                                                                 
  B_tangential = 0.0;                                                                
  C_tangential = 0.0;
}

Delta::~Delta() {}

void Delta::setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in)
{
  Hez = Hez_in;
  L = L_in;
  r = r_in;
}

void Delta::setEffectorOffset(FLOAT_T Ae_in, FLOAT_T Be_in, FLOAT_T Ce_in)
{
  Ae = Ae_in;
  Be = Be_in;
  Ce = Ce_in;
}
  
void Delta::setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in)
{
  A_radial = A_radial_in;                   
  B_radial = B_radial_in;                                                                      
  C_radial = C_radial_in; 
}
void Delta::setTangentError(FLOAT_T A_tangential_in, FLOAT_T B_tangential_in, FLOAT_T C_tangential_in)
{
  A_tangential = A_tangential_in;                                                                 
  B_tangential = B_tangential_in;                                                                
  C_tangential = C_tangential_in;
}

void Delta::recalculate(void)
{
  // Column theta
  const FLOAT_T At = PI / 2.0;
  const FLOAT_T Bt = 7.0 * PI / 6.0;
  const FLOAT_T Ct = 11.0 * PI / 6.0;

  // Calculate the column tangential offsets
  FLOAT_T Apxe = A_tangential;   // Tower A doesn't require a separate y component
  FLOAT_T Apye = 0.00;
  FLOAT_T Bpxe = B_tangential/2.0;
  FLOAT_T Bpye = sqrt(3.0)*(-B_tangential/2.0);
  FLOAT_T Cpxe = sqrt(3.0)*(C_tangential/2.0);
  FLOAT_T Cpye = C_tangential/2.0;

  // Calculate the column positions 
  FLOAT_T Apx = (A_radial + r)*cos(At) + Apxe;
  FLOAT_T Apy = (A_radial + r)*sin(At) + Apye;
  FLOAT_T Bpx = (B_radial + r)*cos(Bt) + Bpxe;
  FLOAT_T Bpy = (B_radial + r)*sin(Bt) + Bpye;
  FLOAT_T Cpx = (C_radial + r)*cos(Ct) + Cpxe;
  FLOAT_T Cpy = (C_radial + r)*sin(Ct) + Cpye;

  // Calculate the effector positions
  FLOAT_T Aex = Ae*cos(At);
  FLOAT_T Aey = Ae*sin(At);
  FLOAT_T Bex = Be*cos(Bt);
  FLOAT_T Bey = Be*sin(Bt);
  FLOAT_T Cex = Ce*cos(Ct);
  FLOAT_T Cey = Ce*sin(Ct);

  // Calculate the virtual column positions
  Avx = Apx - Aex;
  Avy = Apy - Aey;
  Bvx = Bpx - Bex;
  Bvy = Bpy - Bey;
  Cvx = Cpx - Cex;
  Cvy = Cpy - Cey;

  p1 = Vector3(Avx, Avy, 0);
  p2 = Vector3(Bvx, Bvy, 0);
  p3 = Vector3(Cvx, Cvy, 0);
  
  //~ LOG("Delta: Avx = " << Avx << ", Avy = " << Avy << "\n");
  //~ LOG("Delta: Bvx = " << Bvx << ", Bvy = " << Bvy << "\n");
  //~ LOG("Delta: Cvx = " << Cvx << ", Cvy = " << Cvy << "\n");

}

void Delta::inverse_kinematics(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz)
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

void Delta::forward_kinematics(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z)
{
  /* Forward kinematics for Delta Bot. Calculates the X, Y, Z point given
     column translations
  */
    
  p1.z = Az;
  p2.z = Bz;
  p3.z = Cz;
    
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

void Delta::vertical_offset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset)
{
  // vertical offset between circumcenter of carriages and the effector
	
  p1.z = Az;
  p2.z = Bz;
  p3.z = Cz;
    
  // normal to the plane
  Vector3 plane_normal = cross(p1-p2,p2-p3);
  FLOAT_T plane_normal_length = vabs(plane_normal);
  plane_normal /= plane_normal_length;
    
  // radius of circle
  FLOAT_T r = (vabs(p1-p2)*vabs(p2-p3)*vabs(p3-p1))/(2*plane_normal_length);

  // distance below the plane
  *offset = plane_normal.z*sqrt(L*L - r*r);
	
  return;
}
