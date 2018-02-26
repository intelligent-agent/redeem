//
//  PruTimer.h
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__PruTimer__
#define __PathPlanner__PruTimer__

#include <iostream>
#include <queue>
#include <thread>
#include <mutex>
#include <string.h>
#include <strings.h>
#include <condition_variable>
#include <functional>
#include "Logger.h"

//#define DEMO_PRU

class Path;

class PruTimer {
	
	class BlockDef{
	public:
		unsigned long size;
		unsigned long totalTime;
		BlockDef(unsigned long size, unsigned long totalTime) : size(size),totalTime(totalTime) {}
	};
	
	std::string firmwareStepper, firmwareEndstop;
	
	/* Should be locked when used */
	std::queue<BlockDef> blocksID;
	size_t ddr_mem_used;
	size_t totalQueuedMovesTime;
	
	unsigned long ddr_addr;
	unsigned long ddr_size;
	int mem_fd;
	uint8_t *ddr_mem;
	uint8_t *ddr_mem_end;

	uint8_t *shared_mem;
	
	uint8_t *ddr_write_location; //Next available write location
	uint32_t* ddr_nr_events; //location of number of events returned by the PRU
	uint32_t* pru_control;
	
	uint32_t currentNbEvents;

	std::function<void()> endstopAlarmCallback;
	
	std::mutex mutex_memory;
	
	std::condition_variable pruMemoryAvailable;
	size_t blockSizeToWaitFor;

	inline bool isPruMemoryAvailable() {
	  return stop || ddr_size - ddr_mem_used - 8 >= blockSizeToWaitFor + 12;
	}

	inline void notifyIfPruMemoryIsAvailable() {
	  if (isPruMemoryAvailable()) {
	    pruMemoryAvailable.notify_all();
	  }
	}

	std::condition_variable pruMemoryEmpty;

	inline bool isPruMemoryEmpty() {
	  return ddr_mem_used == 0;
	}

	inline void notifyIfPruMemoryIsEmpty() {
	  if (isPruMemoryEmpty()) {
	    pruMemoryEmpty.notify_all();
	  }
	}
	
	std::thread runningThread;
	bool stop;
	
#ifdef DEMO_PRU
	uint8_t *currentReadingAddress;
#endif
	
	void initalizePRURegisters();
	
public:
	PruTimer(std::function<void()> endstopAlarmCallback);
	virtual ~PruTimer();
	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
	
	void run();
	
	void runThread();
	void stopThread(bool join);
	void waitUntilFinished();
	
	size_t getFreeMemory() {
		std::lock_guard<std::mutex> lk(mutex_memory);
		return ddr_size-ddr_mem_used-4;
	}
	
	unsigned long getTotalQueuedMovesTime() {
		std::lock_guard<std::mutex> lk(mutex_memory);
		return totalQueuedMovesTime;
	}

	unsigned int getMaxBytesPerBlock() {
		return (ddr_size / 4) - 12;
	}

	int waitUntilSync();
	
	void suspend();
	
	void resume();
	
	void reset();
	
	void push_block(uint8_t* blockMemory, size_t blockLen, unsigned int unit, unsigned long totalTime);

	size_t getStepsRemaining();
};

#endif /* defined(__PathPlanner__PruTimer__) */
