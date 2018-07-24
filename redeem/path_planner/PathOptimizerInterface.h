#pragma once

#include <vector>

#include "Path.h"

class PathOptimizerInterface
{
public:
    virtual void optimizeBackward(std::vector<Path>& queue, size_t first, size_t last) = 0;
    virtual void optimizeForward(std::vector<Path>& queue, size_t first, size_t last) = 0;
};