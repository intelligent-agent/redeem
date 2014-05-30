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
#include "Logger.h"

class PruTimer {
	/* Should be locked when used */
	std::queue<size_t> ddr_used;
	size_t ddr_mem_used;
	
	unsigned long ddr_addr;
	unsigned long ddr_size;
	int mem_fd;
	uint8_t *ddr_mem;
	uint8_t *ddr_mem_end;
	
	uint8_t *ddr_write_location; //Next available write location
	uint32_t* ddr_nr_events; //location of number of events returned by the PRU
	
	uint32_t currentNbEvents;
	
	std::mutex m;
	
	std::condition_variable blockAvailable;
	
	std::thread runningThread;
	bool stop;
	
public:
	PruTimer();
	virtual ~PruTimer();
	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
	
	void run();
	
	void runThread();
	void stopThread(bool join);
	
	size_t getFreeMemory() {
		std::unique_lock<std::mutex> lk(m);
		return ddr_size-ddr_mem_used-4;
	}
	
	void push_block(uint8_t* blockMemory, size_t blockLen, unsigned int unit);
};

#endif /* defined(__PathPlanner__PruTimer__) */
