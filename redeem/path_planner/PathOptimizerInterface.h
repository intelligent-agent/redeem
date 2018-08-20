#pragma once

#include <vector>

#include "Path.h"

class PathOptimizerInterface
{
public:
    virtual int64_t onPathAdded(std::vector<Path>& queue, size_t first, size_t last) = 0;
    virtual int64_t beforePathRemoval(std::vector<Path>& queue, size_t first, size_t last) = 0;
};
