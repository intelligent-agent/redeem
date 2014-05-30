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

#define DDR_MAGIC			0xbabe7175

PruTimer::PruTimer() {
	ddr_mem = 0;
	mem_fd=-1;
	ddr_addr = 0;
	ddr_size = 0;
	stop = false;
}

bool PruTimer::initPRU(const std::string &firmware_stepper, const std::string &firmware_endstops) {
	std::unique_lock<std::mutex> lk(mutex_memory);
	
#ifdef DEMO_PRU
	ddr_size=0x40000;
	
	ddr_mem = (uint8_t*)malloc(ddr_size);
	ddr_addr = (unsigned long)ddr_mem;
	
	logger << "The DDR memory reserved for the PRU is 0x" << std::hex <<  ddr_size << " and has addr 0x" <<  std::hex <<  ddr_addr << std::endl;
	
	if (ddr_mem == NULL) {
        return false;
    }
	
	ddr_write_location  = ddr_mem;
	ddr_nr_events  = (uint32_t*)(ddr_mem+ddr_size-4);
	ddr_mem_end = ddr_mem+ddr_size-4;
	
	*((uint32_t*)ddr_write_location)=0; //So that the PRU waits
	*ddr_nr_events = 0;
	
	currentReadingAddress = ddr_write_location;
#else
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
    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
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
	
	//bzero(ddr_mem, ddr_size);
	
    /* Execute firmwares on PRU */
    logger << ("\tINFO: Starting stepper firmware on PRU0\r\n");
	ret = prussdrv_exec_program (PRU_NUM0, firmware_stepper.c_str());
	if(ret!=0) {
		logger << "[WARNING] Unable to execute firmware on PRU0" << std::endl;
	}
	
    logger << ("\tINFO: Starting endstop firmware on PRU1\r\n");
    ret=prussdrv_exec_program (PRU_NUM1, firmware_endstops.c_str());
	if(ret!=0) {
		logger << "[WARNING] Unable to execute firmware on PRU1" << std::endl;
	}
	
	//std::this_thread::sleep_for( std::chrono::milliseconds( 1000 ) );
	
	/*prussdrv_pru_wait_event (PRU_EVTOUT_0);
	 
	 printf("\tINFO: PRU0 completed transfer of endstop.\r\n");
	 
	 prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);*/
	
#endif
	
	ddr_mem_used = 0;
	ddr_used = std::queue<size_t>();
	currentNbEvents = 0;
	
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
	size_t nbBlocks = ceil((blockLen+12)/(float)(ddr_size-8));
	
	size_t blockSize = blockLen / nbBlocks;
	
	//Make sure block size is a multiple of unit
	blockSize = (blockSize/unit) * unit;
	
	if(blockSize*nbBlocks<blockLen)
		nbBlocks++;
	
	assert(blockSize*nbBlocks>=blockLen);
	
	size_t nbStepsWritten = 0;
	
	for(int i=0;i<nbBlocks;i++) {
		
		uint8_t *blockStart = blockMemory + i*blockSize;
		
		size_t currentBlockSize;
		
		if(i+1<nbBlocks) {
			currentBlockSize = blockSize;
		} else {
			currentBlockSize = blockLen - i*blockSize;
		}
		
		assert(ddr_size>=currentBlockSize+12);
		
		{
			logger << "Waiting for " << std::dec << currentBlockSize+12 << " bytes available. Currently: " << getFreeMemory() << std::endl;
			
			std::unique_lock<std::mutex> lk(mutex_memory);
			blockAvailable.wait(lk, [this,currentBlockSize]{ return ddr_size-ddr_mem_used-4>=currentBlockSize+12 || stop; });
			
			if(!ddr_mem || stop) return;
			
			
			//Copy at the right location
			if(ddr_write_location+currentBlockSize+12>ddr_mem_end) {
				//Split into two blocks
				
				//First block size
				size_t maxSize = ddr_mem_end-ddr_write_location-8;
				
				//make sure we are in a multiple of unit size
				maxSize = (maxSize/unit)*unit;
				
				ddr_used.push(maxSize+4);
				ddr_mem_used+=maxSize+4;
				
				//First copy the data
				logger << std::hex << "Writing first part of data to 0x" << (unsigned long)ddr_write_location+4 << std::endl;
				memcpy(ddr_write_location+4, blockStart, maxSize);
				
				//Then write on the next free area OF DDR MAGIC
				uint32_t nb = DDR_MAGIC;
				
				assert(ddr_write_location+maxSize+sizeof(nb)*2<=ddr_mem_end);
				
				memcpy(ddr_write_location+maxSize+sizeof(nb), &nb, sizeof(nb));
				
				//Need it?
				msync(ddr_write_location+4, maxSize, MS_SYNC);
				
				//Then signal how much data we have to the PRU
				nb = (uint32_t)maxSize/unit;
				
				nbStepsWritten+=nb;
				
				logger << std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl;
				memcpy(ddr_write_location, &nb, sizeof(nb));
				
				logger << "Written " << std::dec << maxSize << " bytes of stepper commands." << std::endl;
				
				logger << "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl;
				
				msync(ddr_write_location, 4, MS_SYNC);
				
				//It is now the begining
				ddr_write_location=ddr_mem;
				
				size_t remainingSize = currentBlockSize-maxSize;
				
				
				
				if(remainingSize) {
					
					assert(remainingSize == (remainingSize/unit)*unit);
					
					ddr_used.push(remainingSize+4);
					ddr_mem_used+=remainingSize+4;
					
					//First copy the data
					logger << std::hex << "Writing second part of data to 0x" << (unsigned long)ddr_write_location+4 << std::endl;
					memcpy(ddr_write_location+4, blockStart+maxSize, remainingSize);
					
					//Then write on the next free area OF DDR MAGIC
					uint32_t nb = 0;
					
					assert(ddr_write_location+remainingSize+sizeof(nb)*2<=ddr_mem_end);
					
					memcpy(ddr_write_location+remainingSize+sizeof(nb), &nb, sizeof(nb));
					
					//Need it?
					msync(ddr_write_location+sizeof(nb), remainingSize, MS_SYNC);
					
					//Then signal how much data we have to the PRU
					nb = (uint32_t)remainingSize/unit;
					nbStepsWritten+=nb;
					logger << std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl;
					memcpy(ddr_write_location, &nb, sizeof(nb));
					
					logger << "Written " << std::dec << remainingSize << " bytes of stepper commands." << std::endl;
					
					logger << "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl;
					
					msync(ddr_write_location, sizeof(nb), MS_SYNC);
					
					//It is now the begining
					ddr_write_location+=remainingSize+sizeof(nb);
					
				}
				
				
				
			} else {
				
				ddr_used.push(currentBlockSize+4);
				ddr_mem_used+=currentBlockSize+4;
				
				//First copy the data
				logger << std::hex << "Writing data to 0x" << (unsigned long)ddr_write_location+4 << std::endl;
				memcpy(ddr_write_location+4, blockStart, currentBlockSize);
				
				//Then write on the next free area than there is no command to execute
				uint32_t nb = 0;
				
				assert(ddr_write_location+currentBlockSize+sizeof(nb)*2<=ddr_mem_end);
				
				
				memcpy(ddr_write_location+currentBlockSize+sizeof(nb), &nb, sizeof(nb));
				
				//Need it?
				msync(ddr_write_location+sizeof(nb), currentBlockSize, MS_SYNC);
				
				//Then signal how much data we have to the PRU
				nb = (uint32_t)currentBlockSize/unit;
				nbStepsWritten+=nb;
				logger << std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl;
				memcpy(ddr_write_location, &nb, sizeof(nb));
				
				logger << "Written " << std::dec << currentBlockSize << " bytes of stepper commands." << std::endl;
				
				logger << "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl;
				
				ddr_write_location+=currentBlockSize+sizeof(nb);
				
				msync(ddr_write_location, sizeof(nb), MS_SYNC);
				
			}
			
			
		}
	}
	
	assert(nbStepsWritten == blockLen/unit);
	
}

void PruTimer::waitUntilFinished() {
	std::unique_lock<std::mutex> lk(mutex_memory);
	blockAvailable.wait(lk, [this]{return ddr_mem_used==0 || stop; });
}

void PruTimer::run() {
	
	logger << "Starting PruTimer thread..." << std::endl;
	
	while(!stop) {
#ifdef DEMO_PRU
		std::this_thread::sleep_for( std::chrono::milliseconds(300) );
		
		unsigned int* nbCommand = (unsigned int *)currentReadingAddress;
		
		if(!nbCommand)
			continue;
		
		currentReadingAddress+=(*nbCommand)*8+4;
		
		nbCommand = (unsigned int *)currentReadingAddress;
		
		if(*nbCommand == DDR_MAGIC) {
			currentReadingAddress = ddr_mem;
		}
		
		*ddr_nr_events=(*ddr_nr_events)+1;
#else
		prussdrv_pru_wait_event (PRU_EVTOUT_0);
#endif
		if(stop) break;
		
		logger << ("\tINFO: PRU0 completed transfer.\r\n");
		
#ifndef DEMO_PRU
		prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
#endif
		
		msync(ddr_nr_events, 4, MS_SYNC);
		
		uint32_t nb = *ddr_nr_events;
		
		logger << "NB event " << nb << " / " << currentNbEvents << std::endl;
		
		
		
		
		if(currentNbEvents==nb) {
			logger << "[WARNING] Event triggered but counter not incremented" << std::endl;
			msync(ddr_nr_events, 4, MS_SYNC);
			std::this_thread::sleep_for( std::chrono::milliseconds( 1000 ) );
			
			
			nb = *ddr_nr_events;
		}
		
		{
			std::unique_lock<std::mutex> lk(mutex_memory);
			while(currentNbEvents<nb && !ddr_used.empty()) {
				
				ddr_mem_used-=ddr_used.front();
				
				assert(ddr_mem_used<ddr_size);
				
				ddr_used.pop();
				
				
				currentNbEvents++;
			}
		}
		
		currentNbEvents = nb;
		
		logger << "NB event after " << nb << " / " << currentNbEvents << std::endl;
		logger << ddr_mem_used << " bytes used." << std::endl;
		
		blockAvailable.notify_all();
	}
}
