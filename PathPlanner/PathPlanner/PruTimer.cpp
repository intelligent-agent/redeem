//
//  PruTimer.cpp
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#include "PruTimer.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fstream>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <assert.h>
#include "prussdrv.h"
#include "pruss_intc_mapping.h"
#include <cmath>

#define PRU_NUM0	  0
#define PRU_NUM1	  1



PruTimer::PruTimer() {
	ddr_mem = 0;
	mem_fd=-1;
	ddr_addr = 0;
	ddr_size = 0;
	stop = false;
}

bool PruTimer::initPRU(const std::string &firmware_stepper, const std::string &firmware_endstops) {
	std::unique_lock<std::mutex> lk(m);
	
	unsigned int ret;
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;
	
    logger << "Initializing PRU..." << std::endl;
	
    /* Initialize the PRU */
    prussdrv_init ();
	
    /* Open PRU Interrupt */
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret)
    {
        logger << "prussdrv_open failed" << std::endl;
        return false;
    }
	
    /* Get the interrupt initialized */
    prussdrv_pruintc_init(&pruss_intc_initdata);
	
	
	std::ifstream faddr("/sys/class/uio/uio0/maps/map1/addr");
	
	if(!faddr.good()) {
		logger << ("Failed to read /sys/class/uio/uio0/maps/map1/addr\n");
        return false;
	}
	
	std::ifstream fsize("/sys/class/uio/uio0/maps/map1/size");
	
	if(!faddr.good()) {
		logger << ("Failed to read /sys/class/uio/uio0/maps/map1/size\n");
        return false;
	}
	
	std::string s;
	
	std::getline(faddr, s);
	
	ddr_addr = std::stoul(s, nullptr, 16);
	
	std::getline(fsize, s);
	
	ddr_size = std::stoul(s, nullptr, 16);

	logger << "The DDR memory reserved for the PRU is 0x" << std::hex <<  ddr_size << " and has addr 0x" <<  std::hex <<  ddr_addr << std::endl;

    /* open the device */
    mem_fd = open("/dev/mem", O_RDWR);
    if (mem_fd < 0) {
        logger << "Failed to open /dev/mem " << strerror(errno) << std::endl;;
        return false;
    }
	
    /* map the memory */
    ddr_mem = (uint8_t*)mmap(0, ddr_size, PROT_WRITE | PROT_READ, MAP_SHARED, mem_fd, ddr_addr);
    
	if (ddr_mem == NULL) {
        logger << "Failed to map the device "<< strerror(errno) << std::endl;
        close(mem_fd);
        return false;
    }
	
	currentNbEvents = 0;
	
	ddr_write_location  = ddr_mem;
	ddr_nr_events  = (uint32_t*)(ddr_mem+ddr_size-4);
	ddr_mem_end = ddr_mem+ddr_size-4;
	
	*((uint32_t*)ddr_write_location)=0; //So that the PRU waits
	*ddr_nr_events = 0;
	
	//Set DDR location for PRU
	 //pypruss.pru_write_memory(0, 0, [self.ddr_addr, self.ddr_nr_events, 0])
	uint32_t ddrstartData[3];
	ddrstartData[0] = (uint32_t)ddr_addr;
	ddrstartData[1] = (uint32_t)(ddr_addr+ddr_size-4);
	ddrstartData[2] = 0;
	
	prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0, ddrstartData, sizeof(ddrstartData));
	prussdrv_pru_write_memory(PRUSS0_SHARED_DATARAM, 0, ddrstartData, sizeof(ddrstartData));

	
    /* Execute firmwares on PRU */
    logger << ("\tINFO: Executing example on PRU0.\r\n");
    prussdrv_exec_program (PRU_NUM0, firmware_stepper.c_str());
    logger << ("\t\tINFO: Executing example on PRU1.\r\n");
    prussdrv_exec_program (PRU_NUM1, firmware_endstops.c_str());

	/*prussdrv_pru_wait_event (PRU_EVTOUT_0);
	
	printf("\tINFO: PRU0 completed transfer of endstop.\r\n");
	
	prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);*/

	ddr_mem_used = 0;
	ddr_used = std::queue<size_t>();

	
	return true;
}

PruTimer::~PruTimer() {

}


void PruTimer::runThread() {
	stop=false;
	
	if(!ddr_nr_events || !ddr_mem) {
		logger << "Cannot run PruTimer when not initialized" << std::endl;
		return;
	}
	
	runningThread = std::thread([this]() {
		this->run();
	});
}

void PruTimer::stopThread(bool join) {
	logger << "Stopping PruTimer..." << std::endl;
	stop=true;
	
	/* Disable PRU and close memory mapping*/
    prussdrv_pru_disable (PRU_NUM0);
    prussdrv_pru_disable (PRU_NUM1);
    prussdrv_exit ();
	
	if(ddr_mem) {
		munmap(ddr_mem, ddr_size);
		close(mem_fd);
		ddr_mem = 0;
		mem_fd=-1;
	}
    
	logger << "PRU disabled, DDR released, FD closed." << std::endl;
	
	
	blockAvailable.notify_all();
	if(join && runningThread.joinable()) {
		runningThread.join();
	}
	
	logger << "PruTimer stopped." << std::endl;
}

void PruTimer::push_block(uint8_t* blockMemory, size_t blockLen, unsigned int unit) {
	
	if(!ddr_write_location) return;
	
	//Split the block in smaller blocks if needed
	size_t nbBlocks = ceil((blockLen+4)/(float)(ddr_size-8));
	
	size_t blockSize = blockLen / nbBlocks;
	
	for(int i=0;i<nbBlocks;i++) {
		
		uint8_t *blockStart = blockMemory + i*blockSize;
		
		size_t currentBlockSize;
		
		if(i+1<nbBlocks) {
			currentBlockSize = blockSize;
		} else {
			currentBlockSize = blockLen - i*blockSize;
		}
		
		{
			std::unique_lock<std::mutex> lk(m);
			blockAvailable.wait(lk, [this,currentBlockSize]{return ddr_size-ddr_mem_used-4>=currentBlockSize+4 || stop; });
			
			if(!ddr_mem || stop) return;
			
			assert(getFreeMemory()>=currentBlockSize+4);
			
			
			
			//Copy at the right location
			if(ddr_write_location+currentBlockSize+4>ddr_mem_end) {
				//Split into two blocks
				//TODO
			} else {
				
				ddr_used.push(currentBlockSize+4);
				ddr_mem_used+=currentBlockSize+4;
				
				//First copy the data
				logger << std::hex << "Writing data to 0x" << (unsigned long)ddr_write_location << std::endl;
				memcpy(ddr_write_location+4, blockStart, currentBlockSize);
				
				
				//Need it?
				msync(ddr_write_location+4, currentBlockSize, MS_SYNC);
				
				//Then signal how much data we have to the PRU
				uint32_t nb = (uint32_t)currentBlockSize/unit;
				
				logger << std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl;
				memcpy(ddr_write_location, &nb, sizeof(nb));
				
				logger << "Written " << std::dec << nb << " stepper commands." << std::endl;
				
				ddr_write_location+=currentBlockSize+sizeof(nb);
				
				
				
			}
			
			
		}
	}
	
		
	
}

void PruTimer::waitUntilFinished() {
	std::unique_lock<std::mutex> lk(m);
	blockAvailable.wait(lk, [this]{return ddr_mem_used==0 || stop; });
}

void PruTimer::run() {
	while(!stop) {
		prussdrv_pru_wait_event (PRU_EVTOUT_0);
		
		if(stop) break;
		
		logger << ("\tINFO: PRU0 completed transfer.\r\n");
		
		prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
		
		msync(ddr_nr_events, 4, MS_SYNC);
		
		uint32_t nb = *ddr_nr_events;
		
		logger << "NB event " << nb << " / " << currentNbEvents << std::endl;
		
		std::unique_lock<std::mutex> lk(m);

		while(currentNbEvents<nb) {
			
			ddr_mem_used-=ddr_used.front();
			
			assert(ddr_mem_used<ddr_size);
			
			ddr_used.pop();
			
			
			currentNbEvents++;
		}
		
		lk.unlock();
		
		logger << "NB event after " << nb << " / " << currentNbEvents << std::endl;
		logger << ddr_mem_used << " bytes used." << std::endl;
		
		blockAvailable.notify_all();
	}
}
