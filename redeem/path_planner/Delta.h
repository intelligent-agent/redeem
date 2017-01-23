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

#ifndef __DELTA__
#define __DELTA__

#include "config.h"
#include "vector3.h"
#include "Logger.h"

class Delta {
 private:
  FLOAT_T Hez; // Distance head extends below the effector.
  FLOAT_T L; // lenth of rod
  FLOAT_T r; // Radius of columns
	
  FLOAT_T Avx, Avy, Bvx, Bvy, Cvx, Cvy;
  FLOAT_T A_radial, B_radial, C_radial;
  FLOAT_T A_angular, B_angular, C_angular;

  void recalculate();
	
 public:
  Delta();
  ~Delta();

  void setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in);
  void setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in);
  void setAngularError(FLOAT_T A_angular_in, FLOAT_T B_angular_in, FLOAT_T C_angular_in);
  void worldToDelta(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz);
  void deltaToWorld(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z);
  void verticalOffset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset);
};

#endif
