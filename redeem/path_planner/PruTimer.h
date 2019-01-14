//
//  PruTimer.h
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__PruTimer__
#define __PathPlanner__PruTimer__

#include "Logger.h"
#include "PruInterface.h"
#include "config.h"
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <iostream>
#include <mutex>
#include <queue>
#include <string.h>
#include <thread>

//#define DEMO_PRU

class Path;

class PruTimer : public PruInterface
{

    class BlockDef
    {
    public:
        size_t size;
        uint64_t totalTime;
        SyncCallback* callback;
        BlockDef(size_t size, uint64_t totalTime, SyncCallback* callback)
            : size(size)
            , totalTime(totalTime)
            , callback(callback)
        {
        }
    };

    std::string firmwareStepper, firmwareEndstop;

    /* Should be locked when used */
    std::queue<BlockDef> blocksID;
    size_t ddr_mem_used;
    uint64_t totalQueuedMovesTime;
    uint64_t maxQueuedMovesTime = 2 * F_CPU;

    unsigned long ddr_addr;
    unsigned long ddr_size;
    int mem_fd;
    uint8_t* ddr_mem;
    uint8_t* ddr_mem_end;

    uint8_t* shared_mem;

    uint8_t* ddr_write_location; //Next available write location
    uint32_t* ddr_nr_events; //location of number of events returned by the PRU
    uint32_t* pru_control;

    uint32_t currentNbEvents;

    std::function<void()> endstopAlarmCallback;

    std::mutex mutex_memory;

    std::condition_variable pruMemoryAvailable;
    size_t blockSizeToWaitFor;

    inline bool isPruMemoryAvailable()
    {
        return stop || ddr_size - ddr_mem_used - 8 >= blockSizeToWaitFor + 12;
    }

    inline void notifyIfPruMemoryIsAvailable()
    {
        if (isPruMemoryAvailable())
        {
            pruMemoryAvailable.notify_all();
        }
    }

    std::condition_variable pruMemoryEmpty;

    inline bool isPruMemoryEmpty()
    {
        return ddr_mem_used == 0;
    }

    inline void notifyIfPruMemoryIsEmpty()
    {
        if (isPruMemoryEmpty())
        {
            pruMemoryEmpty.notify_all();
        }
    }

    std::condition_variable pruQueueIsntFullByTime;

    inline bool isPruQueueFullByTime()
    {
        return !stop && totalQueuedMovesTime >= maxQueuedMovesTime && blocksID.size() > 1;
    }

    inline void notifyIfPruQueueIsntFullByTime()
    {
        if (!isPruQueueFullByTime())
        {
            pruQueueIsntFullByTime.notify_all();
        }
    }

    std::thread runningThread;
    bool stop;

#ifdef DEMO_PRU
    uint8_t* currentReadingAddress;
#endif

    void initalizePRURegisters();

public:
    PruTimer(std::function<void()> endstopAlarmCallback);
    virtual ~PruTimer();
    bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops) override;

    void run() override;

    void runThread() override;
    void stopThread(bool join) override;
    void waitUntilFinished() override;

    size_t getFreeMemory() override
    {
        std::lock_guard<std::mutex> lk(mutex_memory);
        return ddr_size - ddr_mem_used - 4;
    }

    uint64_t getTotalQueuedMovesTime() override
    {
        std::lock_guard<std::mutex> lk(mutex_memory);
        return totalQueuedMovesTime;
    }

    size_t getMaxBytesPerBlock() override
    {
        return (ddr_size / 4) - 12;
    }

    void suspend() override;

    void resume() override;

    void reset() override;

    void pushBlock(uint8_t* blockMemory, size_t blockLen, unsigned int unit, uint64_t totalTime, SyncCallback* callback = nullptr) override;

    uint32_t getStepsRemaining() override;
    void resetStepsRemaining() override;
};

#endif /* defined(__PathPlanner__PruTimer__) */
