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

#include <queue>

#include "config.h"
#include "vector3.h"
#include "Logger.h"
#include "Path.h"

struct DeltaPathConstants
{
  IntVector3 deltaMotorStart;
  IntVector3 deltaMotorEnd;
  Vector3 deltaStart;
  Vector3 deltaEnd;
  Vector3 worldStart;
  Vector3 worldEnd;
  Vector3 worldStart2;
  Vector3 stepsPerM;
  Vector3 axisSpeeds;
  Vector3 axisSpeeds2;
  Vector3 axisSpeeds3;
  Vector3 axisSpeeds4;
  Vector3 towerX;
  Vector3 towerY;
  Vector3 towerX2;
  Vector3 towerY2;
  FLOAT_T time;
  FLOAT_T axisCore1;
  FLOAT_T axisCore2;
};

class Delta {
 private:
  FLOAT_T Hez; // Distance head extends below the effector.
  FLOAT_T L; // lenth of rod
  FLOAT_T r; // Radius of columns
	
  FLOAT_T Avx, Avy, Bvx, Bvy, Cvx, Cvy;
  FLOAT_T A_radial, B_radial, C_radial;
  FLOAT_T A_angular, B_angular, C_angular;

  void recalculate();
  DeltaPathConstants calculatePathConstants(int axis, const IntVector3& deltaMotorStart, const IntVector3& deltaMotorEnd, const Vector3& stepsPerM, FLOAT_T time) const;
  void calculateSteps(int axis, const DeltaPathConstants& constants, std::vector<Step>& steps) const;
  void calculateStepsInOneDirection(int axis, const DeltaPathConstants& constants, FLOAT_T startTime, FLOAT_T endTime, FLOAT_T towerX, FLOAT_T towerY, FLOAT_T startHeight, FLOAT_T endHeight, std::vector<Step>& steps) const;
  FLOAT_T calculateCriticalPointTimeForAxis(int axis, const DeltaPathConstants& constants) const;
  FLOAT_T calculateStepTime(int axis, const DeltaPathConstants& constants, FLOAT_T towerZ, FLOAT_T minTime, FLOAT_T maxTime) const;
	
 public:
  Delta();
  ~Delta();

  void setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in);
  void setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in);
  void setAngularError(FLOAT_T A_angular_in, FLOAT_T B_angular_in, FLOAT_T C_angular_in);

  Vector3 worldToDelta(const Vector3& pos) const;
  void worldToDelta(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz);
  Vector3 deltaToWorld(const Vector3& pos) const;
  void deltaToWorld(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z);
  IntVector3 worldToDeltaMotorPos(const Vector3& pos, const Vector3& stepsPerM);
  void verticalOffset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset) const;
  void calculateMove(const IntVector3& deltaStart, const IntVector3& deltaEnd, const Vector3& stepsPerM, FLOAT_T speed, std::array<std::vector<Step>, NUM_AXES>& steps) const;
};

#endif
