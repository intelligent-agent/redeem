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
#include "StepperCommand.h"
#include "config.h"

#define PRU_NUM0	  0
#define PRU_NUM1	  1

#define DDR_MAGIC			0xbabe7175

PruTimer::PruTimer() {
	ddr_mem = 0;
	mem_fd=-1;
	ddr_addr = 0;
	ddr_size = 0;
	totalQueuedMovesTime = 0;
	ddr_mem_used = 0;
	stop = false;
}

bool PruTimer::initPRU(const std::string &firmware_stepper, const std::string &firmware_endstops) {
	std::unique_lock<std::mutex> lk(mutex_memory);
	
	firmwareStepper = firmware_stepper;
	firmwareEndstop = firmware_endstops;
	
#ifdef DEMO_PRU
	ddr_size=0x40000;
	
	ddr_mem = (uint8_t*)malloc(ddr_size);
	ddr_addr = (unsigned long)ddr_mem;
	
	LOG( "The DDR memory reserved for the PRU is 0x" << std::hex <<  ddr_size << " and has addr 0x" <<  std::hex <<  ddr_addr << std::endl);
	
	if (ddr_mem == NULL) {
        return false;
    }
	
	ddr_write_location  = ddr_mem;
	ddr_nr_events  = (uint32_t*)(ddr_mem+ddr_size-4);
	ddr_mem_end = ddr_mem+ddr_size-8;
	pru_control = (uint32_t*)(ddr_mem+ddr_size-8);
	
	*((uint32_t*)ddr_write_location)=0; //So that the PRU waits
	*ddr_nr_events = 0;
	
	currentReadingAddress = ddr_write_location;
#else
	unsigned int ret;
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;
	
    LOG( "Initializing PRU..." << std::endl);
	
    /* Initialize the PRU */
    prussdrv_init ();
	
    /* Open PRU Interrupt */
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret)
    {
        LOG( "prussdrv_open failed" << std::endl);
        return false;
    }

    /* Open PRU sync Interrupt */
    ret = prussdrv_open(PRU_EVTOUT_1);
    if (ret)
    {
        LOG( "prussdrv_open failed (sync interrupt)" << std::endl);
        return false;
    }
	
    /* Get the interrupt initialized */
    prussdrv_pruintc_init(&pruss_intc_initdata);
	
	
	std::ifstream faddr("/sys/class/uio/uio0/maps/map1/addr");
	
	if(!faddr.good()) {
		LOG( "Failed to read /sys/class/uio/uio0/maps/map1/addr\n");
        return false;
	}
	
	std::ifstream fsize("/sys/class/uio/uio0/maps/map1/size");
	
	if(!faddr.good()) {
		LOG( "Failed to read /sys/class/uio/uio0/maps/map1/size\n");
        return false;
	}
	
	std::string s;
	
	std::getline(faddr, s);
	
	ddr_addr = std::stoul(s, nullptr, 16);
	
	std::getline(fsize, s);
	
	ddr_size = std::stoul(s, nullptr, 16);
	
	if(!ddr_size || !ddr_addr) {
		LOG("[ERROR] Unable to find DDR address and size for PRU" << std::endl);
		return false;
	}
	
	LOG( "The DDR memory reserved for the PRU is 0x" << std::hex <<  ddr_size << " and has addr 0x" <<  std::hex <<  ddr_addr << std::endl);
	
    /* open the device */
    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd < 0) {
        LOG( "Failed to open /dev/mem " << strerror(errno) << std::endl);;
        return false;
    }
	
    /* map the memory */
    ddr_mem = (uint8_t*)mmap(0, ddr_size, PROT_WRITE | PROT_READ, MAP_SHARED, mem_fd, ddr_addr);
    
	if (ddr_mem == NULL) {
        LOG( "Failed to map the device "<< strerror(errno) << std::endl);
        close(mem_fd);
        return false;
    }
	
	LOG( "Mapped memory starting at 0x" << std::hex << (unsigned long)ddr_mem << std::endl << std::dec);
	
	
	
	ddr_write_location  = ddr_mem;
	ddr_nr_events  = (uint32_t*)(ddr_mem+ddr_size-4);
	ddr_mem_end = ddr_mem+ddr_size-8;
	pru_control = (uint32_t*)(ddr_mem+ddr_size-8);
	
	initalizePRURegisters();
	
	//bzero(ddr_mem, ddr_size);
	
    /* Execute firmwares on PRU */
    LOG( ("\tINFO: Starting stepper firmware on PRU0\r\n"));
	ret = prussdrv_exec_program (PRU_NUM0, firmware_stepper.c_str());
	if(ret!=0) {
		LOG( "[WARNING] Unable to execute firmware on PRU0" << std::endl);
	}
	
    LOG( ("\tINFO: Starting endstop firmware on PRU1\r\n"));
    ret=prussdrv_exec_program (PRU_NUM1, firmware_endstops.c_str());
	if(ret!=0) {
		LOG( "[WARNING] Unable to execute firmware on PRU1" << std::endl);
	}
	
	//std::this_thread::sleep_for( std::chrono::milliseconds( 1000 ) );
	
	/*prussdrv_pru_wait_event (PRU_EVTOUT_0);
	 
	 printf("\tINFO: PRU0 completed transfer of endstop.\r\n");
	 
	 prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);*/
	
#endif
	
	ddr_mem_used = 0;
	blocksID = std::queue<BlockDef>();
	currentNbEvents = 0;
	totalQueuedMovesTime = 0;
	
	return true;
}

void PruTimer::initalizePRURegisters() {
	*((uint32_t*)ddr_write_location)=0; //So that the PRU waits
	*ddr_nr_events = 0;
	*pru_control = 0;
	
	//Set DDR location for PRU
	//pypruss.pru_write_memory(0, 0, [self.ddr_addr, self.ddr_nr_events, 0])
	uint32_t ddrstartData[3];
	ddrstartData[0] = (uint32_t)ddr_addr;
	ddrstartData[1] = (uint32_t)(ddr_addr+ddr_size-4);
	ddrstartData[2] = (uint32_t)(ddr_addr+ddr_size-8); //PRU control register address
	
	prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0, ddrstartData, sizeof(ddrstartData));
	
	
}

PruTimer::~PruTimer() {
	
}

void PruTimer::reset() {
	std::unique_lock<std::mutex> lk(mutex_memory);
	
	prussdrv_pru_disable(0);
	prussdrv_pru_disable(1);
	
	initalizePRURegisters();
	
	/* Execute firmwares on PRU */
    LOG( ("\tINFO: Starting stepper firmware on PRU0\r\n"));
	unsigned int ret = prussdrv_exec_program (PRU_NUM0, firmwareStepper.c_str());
	if(ret!=0) {
		LOG( "[WARNING] Unable to execute firmware on PRU0" << std::endl);
	}
	
    LOG( ("\tINFO: Starting endstop firmware on PRU1\r\n"));
    ret=prussdrv_exec_program (PRU_NUM1, firmwareEndstop.c_str());
	if(ret!=0) {
		LOG( "[WARNING] Unable to execute firmware on PRU1" << std::endl);
	}
	
	totalQueuedMovesTime = 0;
	ddr_mem_used = 0;
	currentNbEvents = 0;
	
	blocksID = std::queue<BlockDef>();
}

void PruTimer::runThread() {
	stop=false;
	
	if(!ddr_nr_events || !ddr_mem) {
		LOG( "Cannot run PruTimer when not initialized" << std::endl);
		return;
	}
	
	runningThread = std::thread([this]() {
		this->run();
	});
}

void PruTimer::stopThread(bool join) {
	LOG( "Stopping PruTimer..." << std::endl);
	stop=true;
	
	/* Disable PRU and close memory mapping*/
    prussdrv_pru_disable (PRU_NUM0);
    prussdrv_pru_disable (PRU_NUM1);
    prussdrv_exit ();
	
	if(ddr_mem) {
#ifdef DEMO_PRU
		free(ddr_mem);
		ddr_mem = NULL;
#else
		munmap(ddr_mem, ddr_size);
		close(mem_fd);
		ddr_mem = NULL;
		mem_fd=-1;
#endif
	}
    
	LOG( "PRU disabled, DDR released, FD closed." << std::endl);
	
	
	blockAvailable.notify_all();
	if(join && runningThread.joinable()) {
		runningThread.join();
	}
	
	LOG( "PruTimer stopped." << std::endl);
}

void PruTimer::push_block(uint8_t* blockMemory, size_t blockLen, unsigned int unit, unsigned int pathID, unsigned long totalTime) {
	
	if(!ddr_write_location) return;
	
	//Split the block in smaller blocks if needed
	size_t nbBlocks = ceil((blockLen+12)/(FLOAT_T)(ddr_size-12));
	
	size_t blockSize = blockLen / nbBlocks;
	
	//Make sure block size is a multiple of unit
	blockSize = (blockSize/unit) * unit;
	
	if(blockSize*nbBlocks<blockLen)
		nbBlocks++;
	
	assert(blockSize*nbBlocks>=blockLen);
	
	size_t nbStepsWritten = 0;
	
	for(unsigned int i=0;i<nbBlocks;i++) {
		
		uint8_t *blockStart = blockMemory + i*blockSize;
		
		size_t currentBlockSize;
		
		if(i+1<nbBlocks) {
			currentBlockSize = blockSize;
		} else {
			currentBlockSize = blockLen - i*blockSize;
		}
		
		assert(ddr_size>=currentBlockSize+12);
		
		{
			//LOG( "Waiting for " << std::dec << currentBlockSize+12 << " bytes available. Currently: " << getFreeMemory() << std::endl);
			
			std::unique_lock<std::mutex> lk(mutex_memory);
			blockAvailable.wait(lk, [this,currentBlockSize]{ return ddr_size-ddr_mem_used-8>=currentBlockSize+12 || stop; });
			
			if(!ddr_mem || stop) return;
			
			
			//Copy at the right location
			if(ddr_write_location+currentBlockSize+12>ddr_mem_end) {
				//Split into two blocks
				
				//First block size
				size_t maxSize = ddr_mem_end-ddr_write_location-8;
				
				//make sure we are in a multiple of unit size
				maxSize = (maxSize/unit)*unit;
				
				bool resetDDR = false;
				
				if(!maxSize) {
					//Dont have the size for a single command! Reset the DDR
					//LOG( "No more space at 0x" << std::hex << ddr_write_location << ". Resetting DDR..." << std::endl);
					uint32_t nb;
	
					//First put 0 for next command
					nb=0;
					memcpy(ddr_mem, &nb, sizeof(nb));
					msync(ddr_mem, sizeof(nb), MS_SYNC);
					
					nb=DDR_MAGIC;
					memcpy(ddr_write_location, &nb, sizeof(nb));
					
					msync(ddr_write_location, sizeof(nb), MS_SYNC);
					
					//It is now the begining
					ddr_write_location=ddr_mem;
					
					resetDDR = true;
					
					if(ddr_write_location+currentBlockSize+12>ddr_mem_end) {
						maxSize = ddr_mem_end-ddr_write_location-8;
						
						//make sure we are in a multiple of unit size
						maxSize = (maxSize/unit)*unit;
					} else {
						maxSize = currentBlockSize;
					}
					
					
				}
				
				assert(maxSize>0);
				unsigned long t = currentBlockSize-maxSize > 0 ? totalTime/2 : totalTime;
				blocksID.emplace(maxSize+4,t); //FIXME: TotalTime is not /2 but doesn't it to be precise to make it work...
				
				ddr_mem_used+=maxSize+4;
				totalQueuedMovesTime += t;
				
				//First copy the data
				//LOG( std::dec << "Writing " << maxSize+4 << " bytes to 0x" << std::hex << (unsigned long)ddr_write_location << std::endl);
				
				memcpy(ddr_write_location+4, blockStart, maxSize);
				
				//Then write on the next free area OF DDR MAGIC
				uint32_t nb;
				
				if(resetDDR) {
					nb=0;
				} else {
					nb=DDR_MAGIC;
				}
				
				assert(ddr_write_location+maxSize+sizeof(nb)*2<=ddr_mem_end);
				
				memcpy(ddr_write_location+maxSize+sizeof(nb), &nb, sizeof(nb));
				
				if(!resetDDR) {
					nb=0;
					memcpy(ddr_mem, &nb, sizeof(nb));
					msync(ddr_mem, sizeof(nb), MS_SYNC);
				}
				
				//Need it?
				msync(ddr_write_location+4, maxSize+4, MS_SYNC);
				
				//Then signal how much data we have to the PRU
				nb = (uint32_t)maxSize/unit;
				
				nbStepsWritten+=nb;
				
				memcpy(ddr_write_location, &nb, sizeof(nb));
				
				//LOG( "Written " << std::dec << maxSize << " bytes of stepper commands." << std::endl);
				
				//LOG( "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl);
				
				msync(ddr_write_location, 4, MS_SYNC);
				
				
				if(resetDDR) {
					ddr_write_location+=maxSize+sizeof(nb);;
				} else {
					//It is now the begining
					ddr_write_location=ddr_mem;
				}
				
				
				size_t remainingSize = currentBlockSize-maxSize;
				
				
				
				if(remainingSize) {
					
					assert(remainingSize == (remainingSize/unit)*unit);

					
					blocksID.emplace(remainingSize+4,totalTime-t); //FIXME: TotalTime is not /2 but doesn't it to be precise to make it work...
					
					ddr_mem_used+=remainingSize+4;
					totalQueuedMovesTime += totalTime-t;
					

					assert(ddr_write_location+remainingSize+sizeof(nb)*2<=ddr_mem_end);
					
					//First copy the data
					//LOG( std::dec << "Writing " << remainingSize+4 << " bytes to 0x" << std::hex << (unsigned long)ddr_write_location << std::endl);
					
					//LOG( std::hex << "Writing second part of data to 0x" << (unsigned long)ddr_write_location+4 << std::endl);
					
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
					//LOG( std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl);
					memcpy(ddr_write_location, &nb, sizeof(nb));
					
					//LOG( "Written " << std::dec << remainingSize << " bytes of stepper commands." << std::endl);
					
					//LOG( "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl);
					
					msync(ddr_write_location, sizeof(nb), MS_SYNC);
					
					//It is now the begining
					ddr_write_location+=remainingSize+sizeof(nb);
					
				}
				
				
				
			} else {
				
				blocksID.emplace(currentBlockSize+4,totalTime); //FIXME: TotalTime is not /2 but doesn't it to be precise to make it work...
				
				ddr_mem_used+=currentBlockSize+4;
				totalQueuedMovesTime += totalTime;


				//First copy the data
				//LOG( std::hex << "Writing data to 0x" << (unsigned long)ddr_write_location+4 << std::endl);
				//LOG( std::dec << "Writing " << currentBlockSize+4 << " bytes to 0x" << std::hex << (unsigned long)ddr_write_location << std::endl);
				
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
				//LOG( std::hex << "Writing nb command to 0x" << (unsigned long)ddr_write_location << std::endl);
				memcpy(ddr_write_location, &nb, sizeof(nb));
				
				//LOG( "Written " << std::dec << currentBlockSize << " bytes of stepper commands." << std::endl);
				
				//LOG( "Remaining free memory: " << std::dec << ddr_size-ddr_mem_used << " bytes." << std::endl);
				
				ddr_write_location+=currentBlockSize+sizeof(nb);
				
				msync(ddr_write_location, sizeof(nb), MS_SYNC);
				
			}
			
			
		}
	}
	
	assert(nbStepsWritten == blockLen/unit);
	
}

void PruTimer::waitUntilFinished() {
	std::unique_lock<std::mutex> lk(mutex_memory);
	blockAvailable.wait(lk, [this]{
        return ddr_mem_used==0 || stop; 
    });
}

void PruTimer::waitUntilLowMoveTime(unsigned long lowMoveTimeTicks) {
	std::unique_lock<std::mutex> lk(mutex_memory);
	blockAvailable.wait(lk, [this,lowMoveTimeTicks]{ /* LOG("Current wait " << totalQueuedMovesTime << "/" << lowMoveTimeTicks <<  std::endl); */ return totalQueuedMovesTime<lowMoveTimeTicks || stop; });
}

void PruTimer::run() {
	
	LOG( "Starting PruTimer thread..." << std::endl);
	
	while(!stop) {
#ifdef DEMO_PRU
		
		unsigned int* nbCommand = (unsigned int *)currentReadingAddress;
		
		if(!nbCommand || stop || !*nbCommand)
			continue;
		SteppersCommand * cmd = (SteppersCommand*)(currentReadingAddress+4);
		FLOAT_T totalWait = 0;
		for(int i=0;i<*nbCommand;i++) {
			totalWait+=cmd->delay/200000.0;
			cmd++;
		}
		
		std::this_thread::sleep_for( std::chrono::milliseconds((unsigned)totalWait) );
		currentReadingAddress+=(*nbCommand)*8+4;
		nbCommand = (unsigned int *)currentReadingAddress;
		if(*nbCommand == DDR_MAGIC) {
			currentReadingAddress = ddr_mem;
		}
		*ddr_nr_events=(*ddr_nr_events)+1;
#else
		unsigned int nbWaitedEvent = prussdrv_pru_wait_event (PRU_EVTOUT_0,1000); // 250ms timeout
#endif

		if(stop) break;
		
		/*
		if (nbWaitedEvent)
			LOG( ("\tINFO: PRU0 completed transfer.\r\n"));
		else
			LOG( ("\tINFO: PRU0 transfer timeout.\r\n"));
		*/
		
		
#ifndef DEMO_PRU
		if(nbWaitedEvent)
			prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
#endif
		
		msync(ddr_nr_events, 4, MS_SYNC);
		uint32_t nb = *ddr_nr_events;
		
		
		
		{
			std::lock_guard<std::mutex> lk(mutex_memory);
			
//			LOG( "NB event " << nb << " / " << currentNbEvents << "\t\tRead event from UIO = " << nbWaitedEvent << ", block in the queue: " << ddr_mem_used << std::endl);

			while(currentNbEvents!=nb && !blocksID.empty()) { //We use != to handle the overflow case
				
				BlockDef & front = blocksID.front();
				
				ddr_mem_used-=front.size;
				totalQueuedMovesTime -=front.totalTime;
				
				assert(ddr_mem_used<ddr_size);
				
//				LOG( "Block of size " << std::dec << front.size << " and time " << front.totalTime << " done." << std::endl);

				blocksID.pop();
				
				currentNbEvents++;
			}
			
			currentNbEvents = nb;
		}
		
		
//		LOG( "NB event after " << std::dec << nb << " / " << currentNbEvents << std::endl);
//		LOG( std::dec <<ddr_mem_used << " bytes used, free: " <<std::dec <<  ddr_size-ddr_mem_used<< "." << std::endl);
		
		blockAvailable.notify_all();
	}
}

int PruTimer::waitUntilSync() {
    int ret;
	// Wait until the PRU sends a sync event.
    ret = prussdrv_pru_wait_event(PRU_EVTOUT_1, 1000);
    if(ret != 0)
    	prussdrv_pru_clear_event(PRU_EVTOUT_1, PRU1_ARM_INTERRUPT); 
    return ret;
}

void PruTimer::suspend() {
	//We lock it so that we are thread safe
	std::unique_lock<std::mutex> lk(mutex_memory);

	*pru_control = 1;
}

void PruTimer::resume() {
	//We lock it so that we are thread safe
	std::unique_lock<std::mutex> lk(mutex_memory);
	
	*pru_control = 0;
}
