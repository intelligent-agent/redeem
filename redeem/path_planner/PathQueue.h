#pragma once
#include <cstdint>
#include <mutex>
#include <vector>

#include "Path.h"
#include "PathOptimizerInterface.h"

template <typename PathOptimizerType, typename std::enable_if<std::is_base_of<PathOptimizerInterface, PathOptimizerType>::value>::type* = nullptr>
class PathQueue
{
private:
    std::mutex mutex;
    PathOptimizerType optimizer;
    std::vector<Path> queue;
    size_t writeIndex;
    size_t readIndex;
    size_t availableSlots;

public:
    PathQueue(size_t size)
        : optimizer(size)
        , queue(size)
        , writeIndex(0)
        , readIndex(0)
        , availableSlots(size)
    {
    }

    size_t availablePathSlots()
    {
        std::lock_guard<std::mutex> lock(mutex);

        return availableSlots;
    }

    void addPath(Path&& path)
    {
        std::lock_guard<std::mutex> lock(mutex);

        queue[writeIndex] = std::move(path);
        writeIndex = (writeIndex + 1) % queue.size();
        availableSlots--;

        optimizer.optimizeBackward(queue, readIndex, writeIndex);
    }

    Path&& popPath()
    {
        std::lock_guard<std::mutex> lock(mutex);

        const size_t currentReadIndex = readIndex;

        optimizer.optimizeForward(queue, readIndex, writeIndex);

        readIndex = (readIndex + 1) % queue.size();
        availableSlots++;

        return std::move(queue[currentReadIndex]);
    }
};