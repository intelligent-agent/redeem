/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
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

#include "../PruTimer.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fstream>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
#include <cmath>
#include "../StepperCommand.h"
#include "../config.h"
#include "PruDump.h"

PruTimer::PruTimer() {
  assert(PruDump::singleton == nullptr);
  PruDump::singleton = new PruDump();
  ddr_size = 1024 * 1024;
}

bool PruTimer::initPRU(const std::string &firmware_stepper, const std::string &firmware_endstops) {
	return true;
}

void PruTimer::initalizePRURegisters() {
}

PruTimer::~PruTimer() {	
}

void PruTimer::reset() {
}

void PruTimer::runThread() {
}

void PruTimer::stopThread(bool join) {
}


/**
blockMemory - the data. 
blockLen - number of data bytes. 
unit - stepSize in bytes. 
pathID - linespos. 
totalTime - time it takes to complete the current block, in ticks. 
*/
void PruTimer::push_block(uint8_t* blockMemory, size_t blockLen, unsigned int unit, unsigned long totalTime) {
  // reverse the block back into an array of StepperCmds

  SteppersCommand* commands = (SteppersCommand*)blockMemory;
  assert(blockLen % sizeof(SteppersCommand) == 0);

  RenderedPath renderedPath;

  renderedPath.stepperCommands.reserve(blockLen / sizeof(SteppersCommand));
  for (size_t i = 0; i < blockLen / sizeof(SteppersCommand); i++) {
    renderedPath.stepperCommands.push_back(commands[i]);
  }

  PruDump::get()->dumpPath(renderedPath);
}

void PruTimer::waitUntilFinished() {
}

void PruTimer::run() {
}

int PruTimer::waitUntilSync() {
  return 0;
}

void PruTimer::suspend() {
}

void PruTimer::resume() {
}
