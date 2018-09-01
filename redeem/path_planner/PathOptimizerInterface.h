#pragma once

#include <vector>

#include "Path.h"
#include "PathQueue.h"

class PathOptimizerInterface
{
public:
    virtual int64_t onPathAdded(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last) = 0;
    virtual int64_t beforePathRemoval(std::vector<Path>& queue, PathQueueIndex first, PathQueueIndex last) = 0;
};
