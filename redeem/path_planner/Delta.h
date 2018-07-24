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
  double time;
  double axisCore1;
  double axisCore2;
};

class Delta {
 private:
  double L; // lenth of rod
  double r; // Radius of columns
	
  double Avx, Avy, Bvx, Bvy, Cvx, Cvy;
  double A_radial, B_radial, C_radial;
  double A_angular, B_angular, C_angular;

  void recalculate();
  DeltaPathConstants calculatePathConstants(int axis, const IntVector3& deltaMotorStart, const IntVector3& deltaMotorEnd, const Vector3& stepsPerM, double time) const;
  void calculateSteps(int axis, const DeltaPathConstants& constants, std::vector<Step>& steps) const;
  void calculateStepsInOneDirection(int axis, const DeltaPathConstants& constants, double startTime, double endTime, double towerX, double towerY, double startHeight, double endHeight, std::vector<Step>& steps) const;
  double calculateCriticalPointTimeForAxis(int axis, const DeltaPathConstants& constants) const;
  double calculateStepTime(int axis, const DeltaPathConstants& constants, double towerZ, double minTime, double maxTime) const;
	
 public:
  Delta();
  ~Delta();

  void setMainDimensions(double L_in, double r_in);
  void setRadialError(double A_radial_in, double B_radial_in, double C_radial_in);
  void setAngularError(double A_angular_in, double B_angular_in, double C_angular_in);

  Vector3 worldToDelta(const Vector3& pos) const;
  void worldToDelta(double X, double Y, double Z, double* Az, double* Bz, double* Cz);
  Vector3 deltaToWorld(const Vector3& pos) const;
  void deltaToWorld(double Az, double Bz, double Cz, double* X, double* Y, double* Z);
  IntVector3 worldToDeltaMotorPos(const Vector3& pos, const Vector3& stepsPerM);
  void verticalOffset(double Az, double Bz, double Cz, double* offset) const;
  void calculateMove(const IntVector3& deltaStart, const IntVector3& deltaEnd, const Vector3& stepsPerM, double speed, std::array<std::vector<Step>, NUM_AXES>& steps) const;
};

#endif
