#include <algorithm>
#include <iostream>
#include <fstream>
#include "PruDump.h"

FLOAT_T testPath(PathPlanner& pathPlanner, FLOAT_T startTime, RenderedPath& path, std::fstream& stepOut);

PruDump* PruDump::singleton;

int errors = 0;
#define CHECK(x, msg) if(!(x)) { std::cerr << "FAILURE: " #x << std::endl << msg << std::endl; errors++; }

PruDump* PruDump::get() {
  return singleton;
}

void PruDump::test(PathPlanner& pathPlanner) {
  std::cout << "I have " << renderedPaths.size() << " paths" << std::endl;
  std::stringstream fileName;
  fileName << "path_all.txt";
  std::fstream stepOut;
  stepOut.open(fileName.str(), std::ios::out | std::ios::trunc);
  std::cout << "writing to " << fileName.str() << std::endl;
  FLOAT_T time = 0;

  for (size_t i = 0; i < renderedPaths.size(); i++) {
    time = testPath(pathPlanner, time, renderedPaths[i], stepOut);
  }

  stepOut.flush();
  stepOut.close();

  std::cout << "Tests counted " << errors << " errors" << std::endl;
}



void PruDump::dumpPath(const RenderedPath& path) {
  renderedPaths.push_back(path);
}

void checkPath(PathPlanner& pathPlanner, Path& path) {
  CHECK(path.areParameterUpToDate(), "path was rendered but stepper parameters were out of date");

}

void checkAccel(int step, int axis, FLOAT_T maxAccel, FLOAT_T thirdStepTime, FLOAT_T secondStepTime, FLOAT_T firstStepTime) {
  /*
  FLOAT_T firstStepSpeed = 1.0 / (secondStepTime - firstStepTime);
  FLOAT_T secondStepSpeed = 1.0 / (thirdStepTime - secondStepTime);

  // the acceleration time spans from the middle of the first step to the middle of the last step
  FLOAT_T accelTime = thirdStepTime - firstStepTime
    - 0.5 * (secondStepTime - firstStepTime)
    - 0.5 * (thirdStepTime - secondStepTime);
  FLOAT_T accel = std::abs(
    (secondStepSpeed - firstStepSpeed) / accelTime);

  // allow 1% deviation from the desired acceleration
  maxAccel *= 1.01;
  */
  /*
  CHECK(accel < maxAccel,
    "speed changed too quickly at step " << step << " on axis " << axis << " - this means we accelerated more quickly than is allowed ("
    << firstStepSpeed << " steps/s to " << secondStepSpeed << " steps/s in " << accelTime << " seconds is a change of " << accel
    << " steps/s^2 which is greater than " << maxAccel << ")");
    */
    
  //std::cout << "axis " << axis << ": " << accel << " must be less than " << maxAccel << " from " << firstStepSpeed
  //  << " steps/s to " << secondStepSpeed << " steps/s in " << accelTime << " seconds" << std::endl;
}

void checkCruise(int step, int axis, FLOAT_T speed, FLOAT_T curStepTime, FLOAT_T lastLastStepTime) {
  FLOAT_T realSpeed = 1.0 / (curStepTime - lastLastStepTime);
  FLOAT_T error = std::abs(realSpeed / speed - 1.0);

  CHECK(error < 0.01,
    "cruise speed had a " << error * 100.0 << "% error at step " << step << " - " << realSpeed << " instead of " << speed << std::endl);

  //std::cout << realSpeed << " must be close to " << speed << std::endl;
}

void printSpeed(std::fstream& stepOut, int axis, bool direction, FLOAT_T secondStepTime, FLOAT_T firstStepTime) {
  stepOut << firstStepTime << "\t";

  for (int i = 0; i < 5; i++)
  {
    if (i == axis)
    {
      stepOut << (direction ? 1.0 : -1.0) / (secondStepTime - firstStepTime) << "\t";
    }
    else
    {
      stepOut << "?\t";
    }
  }

  stepOut << std::endl;
}

void printPosition(std::fstream& stepOut, int axis, FLOAT_T position, FLOAT_T time) {
  stepOut << time << "\t";

  for (int i = 0; i < 5; i++)
  {
    if (i == axis)
    {
      stepOut << position << "\t";
    }
    else
    {
      stepOut << "?\t";
    }
  }

  stepOut << std::endl;
}

FLOAT_T checkTrapezoid(PathPlanner& pathPlanner, Path& path, std::fstream& stepOut, std::vector<SteppersCommand>& stepperCommands, FLOAT_T startTime) {

  std::vector<int> checkDeltas;
  checkDeltas.assign(NUM_AXES, 0);
  std::vector<FLOAT_T> positions;
  positions.assign(NUM_AXES, 0);
  std::vector<FLOAT_T> secondStepTime;
  std::vector<FLOAT_T> firstStepTime;
  std::vector<bool> secondStepDir;
  std::vector<bool> firstStepDir;
  unsigned long long curTicks = 0;

  secondStepTime.assign(NUM_AXES, 0);
  firstStepTime.assign(NUM_AXES, 0);
  secondStepDir.assign(NUM_AXES, false);
  firstStepDir.assign(NUM_AXES, false);

  // pretend we already took three steps at startSpeed
  for (int axis = 0; axis < NUM_AXES; axis++) {
    if (path.isAxisMove(axis)) {
      FLOAT_T axisStartSpeed = path.startSpeed / path.fullSpeed * path.speeds[axis];
      FLOAT_T axisStartInterval = 1.0 / axisStartSpeed;
      secondStepTime[axis] = -1.0 * axisStartInterval;
      secondStepDir[axis] = true;
      firstStepTime[axis] = -2.0 * axisStartInterval;
      firstStepDir[axis] = true;
    }
  }

  for (size_t i = 0; i < stepperCommands.size(); i++) {
    SteppersCommand& command = stepperCommands[i];
    const FLOAT_T curStepTime = curTicks / F_CPU_FLOAT + startTime;

    for (int axis = 0; axis < NUM_AXES; axis++) {
      if (command.step & (1 << axis)) {
	checkDeltas[axis]++;
	bool direction = !!(command.direction & (1 << axis));

	positions[axis] += (direction ? 1.0 : -1.0) / pathPlanner.axisStepsPerM[axis];
	
	//checkAccel(i, axis, path.accels[axis], curStepTime, secondStepTime[axis], firstStepTime[axis]);

	if (secondStepTime[axis] >= 0) {
	  // this skips the synthetic steps
	  //printSpeed(stepOut, axis, secondStepDir[axis], curStepTime, secondStepTime[axis]);
	  printPosition(stepOut, axis, positions[axis], curStepTime);
	}
	/*
	if (curStepTime > path.stepperPath.accelTime && curStepTime < path.stepperPath.accelTime + path.stepperPath.cruiseTime) {
	  // this examines previous steps in groups of two, so we have to skip a few on each side to get a meaningful result
	  checkCruise(i, axis, path.speeds[axis], curStepTime, secondStepTime[axis]);
	}
	*/

	firstStepTime[axis] = secondStepTime[axis];
	firstStepDir[axis] = secondStepDir[axis];
	secondStepTime[axis] = curStepTime;
	secondStepDir[axis] = direction;
      }
    }

    CHECK(command.delay < F_CPU,
      "command delay was over a second: " << command.delay);

    curTicks += command.delay;
  }

  const FLOAT_T finalStepTime = curTicks / F_CPU_FLOAT + startTime;

  for (int axis = 0; axis < NUM_AXES; axis++) {
    if (path.isAxisMove(axis)) {
      //FLOAT_T axisEndSpeed = path.endSpeed / path.fullSpeed * path.speeds[axis];
      //FLOAT_T axisEndInterval = 1.0 / axisEndSpeed;

      //checkAccel(stepperCommands.size(), axis, path.accels[axis], finalStepTime + 1.0 * axisEndInterval, secondStepTime[axis], firstStepTime[axis]);
      //checkAccel(stepperCommands.size() + 1, axis, path.accels[axis], finalStepTime + 2.0 * axisEndInterval, curTicks, secondStepTime[axis]);
      // include one synthetic step here because otherwise we can't get a speed for the final steps
      printSpeed(stepOut, axis, secondStepDir[axis], finalStepTime, secondStepTime[axis]);
    }
  }

  for (int axis = 0; axis < NUM_AXES; axis++) {
    //CHECK(checkDeltas[axis] == path.deltas[axis],
    //  "axis " << axis << " was supposed to step " << path.deltas[axis] << " times, but it stepped " << checkDeltas[axis] << " times.");
  }

  return finalStepTime;
}

FLOAT_T testPath(PathPlanner& pathPlanner, FLOAT_T startTime, RenderedPath& path, std::fstream& stepOut) {
  //CHECK(path.path.getPrimaryAxisSteps() == path.stepperCommands.size(), "rendered step count doesn't match needed step count");
  
  checkPath(pathPlanner, path.path);
  return checkTrapezoid(pathPlanner, path.path, stepOut, path.stepperCommands, startTime);
}