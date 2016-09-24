#include <algorithm>
#include <iostream>
#include "PruDump.h"

void testPath(PathPlanner& pathPlanner, RenderedPath& path);

PruDump* PruDump::singleton;

int errors = 0;
#define CHECK(x, msg) if(!(x)) { std::cerr << "FAILURE: " #x << std::endl << msg << std::endl; errors++; }

PruDump* PruDump::get() {
  return singleton;
}

void PruDump::test(PathPlanner& pathPlanner) {
  std::cout << "I have " << renderedPaths.size() << " paths" << std::endl;

  for (int i = 0; i < renderedPaths.size(); i++) {
    testPath(pathPlanner, renderedPaths[i]);
  }
}



void PruDump::dumpPath(const RenderedPath& path) {
  renderedPaths.push_back(path);
}

void checkPath(PathPlanner& pathPlanner, Path& path) {
  CHECK(path.areParameterUpToDate(), "path was rendered but stepper parameters were out of date");

}

void checkTrapezoid(PathPlanner& pathPlanner, Path& path, std::vector<SteppersCommand>& stepperCommands) {
  double primaryAxisCruiseSpeed = path.speeds[path.primaryAxis] * pathPlanner.axisStepsPerM[path.primaryAxis];
  double primaryAxisStartSpeed = (path.startSpeed / path.fullSpeed) * primaryAxisCruiseSpeed;
  std::cout << "start speed: ideal: " << primaryAxisStartSpeed << " real: " << path.stepperPath.vStart << std::endl;
  double primaryAxisEndSpeed = (path.endSpeed / path.fullSpeed) * primaryAxisCruiseSpeed;

  double idealAccelTime = (primaryAxisCruiseSpeed - primaryAxisStartSpeed) / pathPlanner.maxAccelerationStepsPerSquareSecond[path.primaryAxis];
  std::cout << "accel time: ideal: " << idealAccelTime << " real: " << path.stepperPath.accelSteps / ((path.stepperPath.vStart + path.stepperPath.vMax) / 2.0) << std::endl;

  double primaryAxisAccelSteps = (primaryAxisStartSpeed + primaryAxisCruiseSpeed) / 2.0 * idealAccelTime;
  std::cout << "accel steps: ideal: " << primaryAxisAccelSteps << " real: " << path.stepperPath.accelSteps << std::endl;

  double primaryAxisAccel = (primaryAxisCruiseSpeed - primaryAxisStartSpeed) / idealAccelTime;

  std::cout << "primaryAxisAccel: " << primaryAxisAccel << " max: " << pathPlanner.maxAccelerationStepsPerSquareSecond[path.primaryAxis] << std::endl;

  double lastInterval = F_CPU / primaryAxisStartSpeed;
  double lastSpeed = primaryAxisStartSpeed;

  for (unsigned int i = 0; i <= path.primaryAxisSteps; i++) {
    double speed = 0;
    double accelTime = 0;
    if (i == path.primaryAxisSteps) {
      speed = primaryAxisEndSpeed;
      accelTime = ((F_CPU / primaryAxisEndSpeed) + lastInterval) / (double)F_CPU;
    }
    else {
      speed = (double)F_CPU / stepperCommands[i].delay;
      accelTime = (stepperCommands[i].delay + lastInterval) / (double)F_CPU;
    }

    double accel = std::abs((speed - lastSpeed) / accelTime);

    std::cout << speed << " - " << lastSpeed << " / " << accelTime << " = " << accel
      << " must be less than " << primaryAxisAccel << std::endl;

    CHECK(accel < primaryAxisAccel,
      "speed changed too quickly at step " << i << " - this means we accelerated more quickly than is allowed ("
      << lastSpeed << " steps/s to " << speed << " steps/s in " << accelTime << " seconds is a change of " << accel << " steps/s^2 which is greater than " << primaryAxisAccel << ")");

    lastInterval = stepperCommands[i].delay;
    lastSpeed = speed;
  }
}

void testPath(PathPlanner& pathPlanner, RenderedPath& path) {
  CHECK(path.path.getPrimaryAxisSteps() == path.stepperCommands.size(), "rendered step count doesn't match needed step count");
  
  checkPath(pathPlanner, path.path);
  checkTrapezoid(pathPlanner, path.path, path.stepperCommands);
}