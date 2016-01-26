
/*
 This file is part of Redeem - 3D Printer control software

 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html


 This file is based on Repetier-Firmware licensed under GNU GPL v3 and
 available at https://github.com/repetier/Repetier-Firmware

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

 #include "Path.h"

 Path::Path() {
    joinFlags = 0;
	primaryAxis = 0;
    timeInTicks = 0;
    dir = 0;

    for (size_t axis=0; axis < NUM_AXIS; ++axis) {
        delta[axis] = 0;
        error[axis] = 0;
        startPos[axis] = 0;
        endPos[axis] = 0;
    }
    speed = 0;
    speedX = 0;
    speedY = 0;
    speedZ = 0;
    speedE = 0;
    speedH = 0;
    fullSpeed = 0;
    invFullSpeed = 0;
    accelerationDistance2 = 0;
    maxJunctionSpeed = 0;
    startSpeed = 0;
    endSpeed = 0;
    minSpeed = 0;
    distance = 0;
    fullInterval = 0;
    accelSteps = 0;
    decelSteps = 0;
    accelerationPrim = 0;
    fAcceleration = 0;
    vMax = 0;
    vStart = 0;
    vEnd = 0;
    stepsRemaining = 0;
    commands.clear();
 }

 Path::Path(const Path& path){
    // copy constructor

    joinFlags = path.joinFlags;
	primaryAxis = path.primaryAxis;
    timeInTicks = path.timeInTicks;
    dir = path.dir;

    for (size_t axis=0; axis < NUM_AXIS; ++axis) {
        delta[axis] = path.delta[axis];
        error[axis] = path.error[axis];
        startPos[axis] = path.startPos[axis];
        endPos[axis] = path.endPos[axis];
    }
    speed = path.speed;
    speedX = path.speedX;
    speedY = path.speedY;
    speedZ = path.speedZ;
    speedE = path.speedE;
    speedH = path.speedH;
    fullSpeed = path.fullSpeed;
    invFullSpeed = path.invFullSpeed;
    accelerationDistance2 = path.accelerationDistance2;
    maxJunctionSpeed = path.maxJunctionSpeed;
    startSpeed = path.startSpeed;
    endSpeed = path.endSpeed;
    minSpeed = path.minSpeed;
    distance = path.distance;
    fullInterval = path.fullInterval;
    accelSteps = path.accelSteps;
    decelSteps = path.decelSteps;
    accelerationPrim = path.accelerationPrim;
    fAcceleration = path.fAcceleration;
    vMax = path.vMax;
    vStart = path.vStart;
    vEnd = path.vEnd;
    stepsRemaining = path.stepsRemaining;
    commands = path.commands;
 }
