#pragma once

#include <cstdint>
#include <string>

#include "SyncCallback.h"

class PruInterface
{
public:
    virtual ~PruInterface()
    {
    }
    virtual bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops) = 0;

    virtual void run() = 0;

    virtual void runThread() = 0;
    virtual void stopThread(bool join) = 0;
    virtual void waitUntilFinished() = 0;

    virtual size_t getFreeMemory() = 0;

    virtual uint64_t getTotalQueuedMovesTime() = 0;

    virtual size_t getMaxBytesPerBlock() = 0;

    virtual void suspend() = 0;

    virtual void resume() = 0;

    virtual void reset() = 0;

    virtual void pushBlock(uint8_t* blockMemory, size_t blockLen, unsigned int unit, uint64_t totalTime, SyncCallback* callback = nullptr) = 0;

    virtual size_t getStepsRemaining() = 0;
};