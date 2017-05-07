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
#include "vectorN.h"
#include "Path.h"
#include "Logger.h"

#define _USE_MATH_DEFINES
#include <math.h>
#include <assert.h>
#include <algorithm>

void calculateLinearMove(const int axis, const long long startStep, const long long endStep, const FLOAT_T time, std::vector<Step>& steps);

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

Vector3 Delta::worldToDelta(const Vector3& pos) const
{
  /*
    Inverse kinematics for Delta bot. Returns position for column
    A, B, and C
  */
    
  const FLOAT_T L2 = L*L;
    
  const FLOAT_T XA = pos.x - Avx;
  const FLOAT_T XB = pos.x - Bvx;
  const FLOAT_T XC = pos.x - Cvx;
    
  const FLOAT_T YA = pos.y - Avy;
  const FLOAT_T YB = pos.y - Bvy;
  const FLOAT_T YC = pos.y - Cvy;

  // Calculate the translation in carriage position
  const FLOAT_T Acz = sqrt(L2 - XA*XA - YA*YA);
  const FLOAT_T Bcz = sqrt(L2 - XB*XB - YB*YB);
  const FLOAT_T Ccz = sqrt(L2 - XC*XC - YC*YC);

  const FLOAT_T offset = pos.z + Hez;

  // Calculate the position of the carriages
  return Vector3(Acz + offset, Bcz + offset, Ccz + offset);
  
  //~ LOG("Delta: Az = " << *Az << "\n");
  //~ LOG("Delta: Bz = " << *Bz << "\n");
  //~ LOG("Delta: Cz = " << *Cz << "\n");
}

void Delta::worldToDelta(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz)
{
  const Vector3 result = worldToDelta(Vector3(X, Y, Z));
  *Az = result.x;
  *Bz = result.y;
  *Cz = result.z;
}

Vector3 Delta::deltaToWorld(const Vector3& pos) const
{
  /* Forward kinematics for Delta Bot. Calculates the X, Y, Z point given
     column translations
  */

  const Vector3 p1 = Vector3(Avx, Avy, pos.x);
  const Vector3 p2 = Vector3(Bvx, Bvy, pos.y);
  const Vector3 p3 = Vector3(Cvx, Cvy, pos.z);

  const Vector3 p12 = p2 - p1;
  const Vector3 p13 = p3 - p1;
    
  const FLOAT_T d = vabs(p12);
    
  const Vector3 ex = p12/d;
    
  const FLOAT_T i = dot(ex, p13);
  const Vector3 iex = i*ex;
    
    
  const Vector3 ey = (p13 - iex) / vabs(p13 - iex);
  const Vector3 ez = cross(ex, ey);
    
  const FLOAT_T j = dot(ey, p13);
    
  const FLOAT_T x = d/2.0;
  const FLOAT_T y = ((i*i + j*j)/2.0 - i*x)/j;
  const FLOAT_T z = sqrt(L*L - x*x - y*y);
    
  const Vector3 effector = p1 + x*ex + y*ey - z*ez;
  
  return effector;
}

void Delta::deltaToWorld(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z)
{
  const Vector3 result = deltaToWorld(Vector3(Az, Bz, Cz));
  *X = result.x;
  *Y = result.y;
  *Z = result.z;
}

IntVector3 Delta::worldToDeltaMotorPos(const Vector3& pos, const Vector3& stepsPerM)
{
  const Vector3 deltaPos = worldToDelta(pos);
  return (deltaPos * stepsPerM).round();
}


void Delta::verticalOffset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset) const
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



DeltaPathConstants Delta::calculatePathConstants(int axis, const IntVector3& deltaMotorStart, const IntVector3& deltaMotorEnd, const Vector3& stepsPerM, FLOAT_T time) const
{
  DeltaPathConstants result;
  result.deltaMotorStart = deltaMotorStart;
  result.deltaMotorEnd = deltaMotorEnd;
  result.deltaStart = deltaMotorStart.toVector3() / stepsPerM;
  result.deltaEnd = deltaMotorEnd.toVector3() / stepsPerM;
  result.worldStart = deltaToWorld(result.deltaStart);
  result.worldEnd = deltaToWorld(result.deltaEnd);
  result.worldStart2 = result.worldStart * result.worldStart;
  result.stepsPerM = stepsPerM;
  result.axisSpeeds = (result.worldEnd - result.worldStart) / time;
  result.axisSpeeds2 = result.axisSpeeds * result.axisSpeeds;
  result.axisSpeeds3 = result.axisSpeeds2 * result.axisSpeeds;
  result.axisSpeeds4 = result.axisSpeeds3 * result.axisSpeeds;
  result.towerX = Vector3(Avx, Bvx, Cvx);
  result.towerY = Vector3(Avy, Bvy, Cvy);
  result.towerX2 = result.towerX * result.towerX;
  result.towerY2 = result.towerY * result.towerY;

  const DeltaPathConstants& c = result;
  const FLOAT_T& Xo = c.worldStart.x;
  const FLOAT_T& Yo = c.worldStart.y;
  const FLOAT_T& Zo = c.worldStart.z;
  const FLOAT_T& Xo2 = c.worldStart2.x;
  const FLOAT_T& Yo2 = c.worldStart2.y;
  const FLOAT_T& Zo2 = c.worldStart2.z;
  const FLOAT_T& Xd = c.axisSpeeds.x;
  const FLOAT_T& Yd = c.axisSpeeds.y;
  const FLOAT_T& Zd = c.axisSpeeds.z;
  const FLOAT_T& Xd2 = c.axisSpeeds2.x;
  const FLOAT_T& Yd2 = c.axisSpeeds2.y;
  const FLOAT_T& Zd2 = c.axisSpeeds2.z;

  const FLOAT_T L2 = L * L;

  const FLOAT_T& towerX = c.towerX[axis];
  const FLOAT_T& towerY = c.towerY[axis];
  const FLOAT_T& towerX2 = c.towerX2[axis];
  const FLOAT_T& towerY2 = c.towerY2[axis];

  result.axisCore1 = (-Yd2 - Xd2)*Zo2 + (2 * Yd*Yo - 2 * towerY*Yd + 2 * Xd*Xo - 2 * towerX*Xd)*Zd*Zo + (-Yo2 + 2 * towerY*Yo - Xo2 + 2 * towerX*Xo + L2 - towerY2 - towerX2)*Zd2 - Xd2*Yo2 + ((2 * Xd*Xo - 2 * towerX*Xd)*Yd + 2 * towerY*Xd2)*Yo + (-Xo2 + 2 * towerX*Xo + L2 - towerX2)*Yd2 +
    (2 * towerX*towerY*Xd - 2 * towerY*Xd*Xo)*Yd + (L2 - towerY2)*Xd2;

  result.axisCore2 = ((2 * Yd2 + 2 * Xd2)*Zo + (-2 * Yd*Yo + 2 * towerY*Yd - 2 * Xd*Xo + 2 * towerX*Xd)*Zd);


  result.time = time;
  return result;
}

void Delta::calculateMove(const IntVector3& deltaStart, const IntVector3& deltaEnd, const Vector3& stepsPerM, FLOAT_T time, std::array<std::vector<Step>, NUM_AXES>& steps) const
{
  auto const timestamp = std::chrono::system_clock::now();
  const DeltaPathConstants c = calculatePathConstants(0, deltaStart, deltaEnd, stepsPerM, time);

  if (deltaStart == deltaEnd)
  {
    // no motion platform movement - this might be a retraction or somesuch
    return;
  }
  if (c.worldStart.x == c.worldEnd.x && c.worldStart.y == c.worldEnd.y)
  {
    for (int axis = 0; axis < 3; axis++)
    {
      LOG("no XY move - calculating Z move as linear" << std::endl);
      calculateLinearMove(axis, deltaStart[axis], deltaEnd[axis], time, steps[axis]);
    }
  }
  else
  {
    LOG("XY move - doing full delta math, move should take " << time << std::endl);

    for (int axis = 0; axis < 3; axis++)
    {
      const DeltaPathConstants c = calculatePathConstants(axis, deltaStart, deltaEnd, stepsPerM, time);
      calculateSteps(axis, c, steps[axis]);
    }
  }

  auto const timeTaken = std::chrono::system_clock::now() - timestamp;
  LOG("calculating move took " << std::chrono::duration_cast<std::chrono::milliseconds>(timeTaken).count() << " ms" << std::endl);
}

void Delta::calculateSteps(int axis, const DeltaPathConstants& c, std::vector<Step>& steps) const
{
  assert(axis >= 0 && axis <= 2);

  const FLOAT_T towerX = (axis == 0 ? Avx : (axis == 1 ? Bvx : Cvx));
  const FLOAT_T towerY = (axis == 0 ? Avy : (axis == 1 ? Bvy : Cvy));

  const FLOAT_T criticalPointTime = calculateCriticalPointTimeForAxis(axis, c);

  assert(steps.empty());

  if (std::isnan(criticalPointTime) || criticalPointTime <= 0 || criticalPointTime >= c.time)
  {
    LOG("axis " << axis << " has no critical point - calculating steps from " << c.deltaStart[axis] << " to " << c.deltaEnd[axis] << std::endl);
    // easy case - axis has no critical point
    steps.reserve(std::abs(c.deltaMotorEnd[axis] - c.deltaMotorStart[axis]));

    calculateStepsInOneDirection(axis, c, 0, c.time,
      towerX, towerY, c.deltaStart[axis], c.deltaEnd[axis], steps);
  }
  else
  {
    const Vector3 criticalPointCartesianPosition = c.worldStart + (c.axisSpeeds * criticalPointTime);
    const Vector3 criticalPointDeltaPosition = worldToDelta(criticalPointCartesianPosition);
    const FLOAT_T criticalPointHeight = criticalPointDeltaPosition[axis];
    const long long criticalPointMotorPos = std::llround(criticalPointHeight * c.stepsPerM[axis]);

    LOG("axis " << axis << " has a critical point at " << criticalPointTime << " - calculating steps from " << c.deltaStart[axis] << " to " << criticalPointHeight << " to " << c.deltaEnd[axis] << std::endl);
    steps.reserve(std::abs(c.deltaMotorStart[axis] - criticalPointMotorPos) + std::abs(criticalPointMotorPos - c.deltaMotorEnd[axis]));

    calculateStepsInOneDirection(axis, c, 0, criticalPointTime,
      towerX, towerY, c.deltaStart[axis], criticalPointHeight, steps);

    calculateStepsInOneDirection(axis, c, criticalPointTime, c.time,
      towerX, towerY, criticalPointHeight, c.deltaEnd[axis], steps);

  }

}

void Delta::calculateStepsInOneDirection(int axis, const DeltaPathConstants& c, FLOAT_T startTime, FLOAT_T endTime, FLOAT_T towerX, FLOAT_T towerY, FLOAT_T startHeight, FLOAT_T endHeight, std::vector<Step>& steps) const
{
  const bool direction = startHeight < endHeight;

  const long long startStep = std::llroundl(startHeight * c.stepsPerM[axis]); // m * (steps/m) = step
  const long long endStep = std::llroundl(endHeight * c.stepsPerM[axis]);

  const long long stepIncrement = direction ? 1 : -1;
  const FLOAT_T stepOffset = stepIncrement / 2.0;
  
  long long step = startStep;
  FLOAT_T time = startTime;
  
  while (step != endStep)
  {
    const FLOAT_T height = (step + stepOffset) / c.stepsPerM[axis];

    time = calculateStepTime(axis, c, height, time, endTime);

    assert(steps.empty() || time > steps.back().time);

    steps.emplace_back(Step(time, axis, direction));

    assert(!std::isnan(time));
    assert(time <= endTime);

    step += stepIncrement;
  }
}

FLOAT_T Delta::calculateCriticalPointTimeForAxis(int axis, const DeltaPathConstants& c) const
{
  // These are convenience names to make the math more readable
  const FLOAT_T& Xo = c.worldStart.x;
  const FLOAT_T& Yo = c.worldStart.y;
  const FLOAT_T& Xo2 = c.worldStart2.x;
  const FLOAT_T& Yo2 = c.worldStart2.y;
  const FLOAT_T& Xd = c.axisSpeeds.x;
  const FLOAT_T& Yd = c.axisSpeeds.y;
  const FLOAT_T& Zd = c.axisSpeeds.z;
  const FLOAT_T& Xd2 = c.axisSpeeds2.x;
  const FLOAT_T& Yd2 = c.axisSpeeds2.y;
  const FLOAT_T& Zd2 = c.axisSpeeds2.z;
  const FLOAT_T& Xd3 = c.axisSpeeds3.x;
  const FLOAT_T& Yd3 = c.axisSpeeds3.y;
  const FLOAT_T& Xd4 = c.axisSpeeds4.x;
  const FLOAT_T& Yd4 = c.axisSpeeds4.y;;

  const FLOAT_T L2 = L * L;

  const FLOAT_T& towerX = c.towerX[axis];
  const FLOAT_T& towerY = c.towerY[axis];
  const FLOAT_T& towerX2 = c.towerX2[axis];
  const FLOAT_T& towerY2 = c.towerY2[axis];
    
  if (c.axisSpeeds[2] == 0)
  {
    return -(Yd*Yo - towerY*Yd + Xd*Xo - towerX*Xd) / (Yd2 + Xd2);
  }
  else
  {
    // With a Z move, there are two possible solutions, but we'll only want zero or one of them.

    const FLOAT_T firstT = -(std::sqrt(-Xd2 * Yo2 + ((2 * Xd*Xo - 2 * towerX*Xd)*Yd + 2 * towerY*Xd2)*Yo + (-Xo2 + 2 * towerX*Xo + L2 - towerX2)*Yd2 + (2 * towerX*towerY*Xd - 2 * towerY*Xd*Xo)*Yd + (L2 - towerY2)*Xd2)*Zd*std::sqrt(Zd2 + Yd2 + Xd2) + (Yd*Yo - towerY*Yd + Xd*Xo - towerX*Xd)*Zd2 + (Yd3 + Xd2 * Yd)*Yo - towerY*Yd3 + (Xd*Xo - towerX*Xd)*Yd2 - towerY*Xd2 * Yd + Xd3 * Xo - towerX*Xd3) / ((Yd2 + Xd2)*Zd2 + Yd4 + 2 * Xd2 * Yd2 + Xd4);
    const FLOAT_T secondT = (std::sqrt(-Xd2 * Yo2 + ((2 * Xd*Xo - 2 * towerX*Xd)*Yd + 2 * towerY*Xd2)*Yo + (-Xo2 + 2 * towerX*Xo + L2 - towerX2)*Yd2 + (2 * towerX*towerY*Xd - 2 * towerY*Xd*Xo)*Yd + (L2 - towerY2)*Xd2)*Zd*std::sqrt(Zd2 + Yd2 + Xd2) + (-Yd*Yo + towerY*Yd - Xd*Xo + towerX*Xd)*Zd2 + (-Yd3 - Xd2 * Yd)*Yo + towerY*Yd3 + (towerX*Xd - Xd*Xo)*Yd2 + towerY*Xd2 * Yd - Xd3 * Xo + towerX*Xd3) / ((Yd2 + Xd2)*Zd2 + Yd4 + 2 * Xd2 * Yd2 + Xd4);

    assert(!std::isnan(firstT) && !std::isnan(secondT));

    if (firstT > 0 && firstT <= c.time)
    {
      return firstT;
    }
    else
    {
      return secondT;
    }
  }
  
}

FLOAT_T Delta::calculateStepTime(int axis, const DeltaPathConstants& c, FLOAT_T towerZ, FLOAT_T minTime, FLOAT_T maxTime) const
{
  const FLOAT_T& Xo = c.worldStart.x;
  const FLOAT_T& Yo = c.worldStart.y;
  const FLOAT_T& Zo = c.worldStart.z;
  const FLOAT_T& Xd = c.axisSpeeds.x;
  const FLOAT_T& Yd = c.axisSpeeds.y;
  const FLOAT_T& Zd = c.axisSpeeds.z;
  const FLOAT_T& Xd2 = c.axisSpeeds2.x;
  const FLOAT_T& Yd2 = c.axisSpeeds2.y;
  const FLOAT_T& Zd2 = c.axisSpeeds2.z;

  const FLOAT_T& towerX = c.towerX[axis];
  const FLOAT_T& towerY = c.towerY[axis];

  const FLOAT_T towerZ2 = towerZ * towerZ;
  /*
  The original formula here is that a delta move from (Xo, Yo, Zo) at speed (Xd, Yd, Zd)
  will be at point (towerX, towerY, towerZ) at these times:

  t1 = -(sqrt((-Yd2-Xd2)*Zo2+((2*Yd*Yo-2*towerY*Yd+2*Xd*Xo-2*towerX*Xd)*Zd+2*towerZ*Yd2+2*towerZ*Xd2)*Zo+(-Yo2+2*towerY*Yo-Xo2+2*towerX*Xo+L2-towerY2-towerX2)*Zd2+
  (-2*towerZ*Yd*Yo+2*towerZ*towerY*Yd-2*towerZ*Xd*Xo+2*towerZ*towerX*Xd)*Zd-Xd2*Yo2+((2*Xd*Xo-2*towerX*Xd)*Yd+2*towerY*Xd2)*Yo+(-Xo2+2*towerX*Xo+L2-towerX2-towerZ2)*Yd2+(2*towerX*towerY*Xd-2*towerY*Xd*Xo)*Yd+(L2-towerY2-towerZ2)*Xd2)+Zd*Zo-towerZ*
  Zd+Yd*Yo-towerY*Yd+Xd*Xo-towerX*Xd)/(Zd2+Yd2+Xd2)
  t2 = (sqrt((-Yd2-Xd2)*Zo2+((2*Yd*Yo-2*towerY*Yd+2*Xd*Xo-2*towerX*Xd)*Zd+2*towerZ*Yd2+2*towerZ*Xd2)*Zo+(-Yo2+2*towerY*Yo-Xo2+2*towerX*Xo+L2-towerY2-towerX2)*Zd2+
  (-2*towerZ*Yd*Yo+2*towerZ*towerY*Yd-2*towerZ*Xd*Xo+2*towerZ*towerX*Xd)*Zd-Xd2*Yo2+((2*Xd*Xo-2*towerX*Xd)*Yd+2*towerY*Xd2)*Yo+(-Xo2+2*towerX*Xo+L2-towerX2-towerZ2)*Yd2+(2*towerX*towerY*Xd-2*towerY*Xd*Xo)*Yd+(L2-towerY2-towerZ2)*Xd2)-Zd*Zo+towerZ*
  Zd-Yd*Yo+towerY*Yd-Xd*Xo+towerX*Xd)/(Zd2+Yd2+Xd2)

  That's long and painful, so we split it into these pieces:

  core=(-Yd2-Xd2)*Zo2+((2*Yd*Yo-2*towerY*Yd+2*Xd*Xo-2*towerX*Xd)*Zd+2*towerZ*Yd2+2*towerZ*Xd2)*Zo+(-Yo2+2*towerY*Yo-Xo2+2*towerX*Xo+L2-towerY2-towerX2)*Zd2+
  (-2*towerZ*Yd*Yo+2*towerZ*towerY*Yd-2*towerZ*Xd*Xo+2*towerZ*towerX*Xd)*Zd-Xd2*Yo2+((2*Xd*Xo-2*towerX*Xd)*Yd+2*towerY*Xd2)*Yo+(-Xo2+2*towerX*Xo+L2-towerX2-towerZ2)*Yd2+(2*towerX*towerY*Xd-2*towerY*Xd*Xo)*Yd+(L2-towerY2-towerZ2)*Xd2
  denominator=Zd2+Yd2+Xd2
  t1 = -(sqrt(core+Zd*Zo-towerZ*Zd+Yd*Yo-towerY*Yd+Xd*Xo-towerX*Xd)/denominator
  t2 = (sqrt(core+-Zd*Zo+towerZ*Zd-Yd*Yo+towerY*Yd-Xd*Xo+towerX*Xd)/denominator

  For a given move, the only variables that will change will be towerX and towerY (which change for every axis) and towerZ (which changes for every step).
  With this in mind, we can further subdivide this:

  axisCore = (-Yd2 - Xd2)*Zo2
    + (-Yo2 + 2 * towerY*Yo - Xo2 + 2 * towerX*Xo + L2 - towerY2 - towerX2)*Zd2
    - Xd2*Yo2
    + ((2 * Xd*Xo - 2 * towerX*Xd)*Yd + 2 * towerY*Xd2)*Yo
    + (2 * towerX*towerY*Xd - 2 * towerY*Xd*Xo)*Yd
    + L2*Xd2
    - Xd2*towerY2
    - 2 * Yd*Zd*Zo*towerY
    - Yd2*towerX2
    - (2 * Xd*Zd*Zo - 2 * Xo*Yd2)*towerX
    - (-2 * Yd*Yo - 2 * Xd*Xo)*Zd*Zo
    - (Xo2 - L2)*Yd2;

  axisCore2 = -2 * Yd*Zd*towerY - 2 * Xd*Zd*towerX + (-2 * Yd2 - 2 * Xd2)*Zo + (2 * Yd*Yo + 2 * Xd*Xo)*Zd;

  auto core = axisCore
    - (Yd2 + Xd2)*towerZ2
    - axisCore2*towerZ;

    auto denominator = (Zd2 + Yd2 + Xd2);
    auto t1 = -(sqrt(core + Zd*Zo - towerZ*Zd + Yd*Yo - towerY*Yd + Xd*Xo - towerX*Xd) / denominator;
    auto t2 = (sqrt(core + -Zd*Zo + towerZ*Zd - Yd*Yo + towerY*Yd - Xd*Xo + towerX*Xd) / denominator;


  */

  const FLOAT_T core = std::sqrt(c.axisCore1 + c.axisCore2 * towerZ - (Xd2 + Yd2)*towerZ2);

  const FLOAT_T denominator = (Zd2 + Yd2 + Xd2);

  const FLOAT_T firstTime = -(core + Zd*Zo - towerZ*Zd + Yd*Yo - towerY*Yd + Xd*Xo - towerX*Xd) / denominator;
  const FLOAT_T secondTime = (core + -Zd*Zo + towerZ*Zd - Yd*Yo + towerY*Yd - Xd*Xo + towerX*Xd) / denominator;

  assert(!std::isnan(firstTime) && !std::isnan(secondTime));

  const FLOAT_T smallerTime = std::min(firstTime, secondTime);
  const FLOAT_T largerTime = std::max(firstTime, secondTime);

  if (std::isnan(firstTime))
  {
    return secondTime;
  }
  else if (std::isnan(secondTime))
  {
    return firstTime;
  }
  else if (smallerTime > minTime)
  {
    assert(largerTime > maxTime);
    return smallerTime;
  }
  else
  {
    return largerTime;
  }
}
