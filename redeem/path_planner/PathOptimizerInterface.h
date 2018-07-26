#pragma once

#include <vector>

#include "Path.h"

class PathOptimizerInterface
{
public:
    virtual void onPathAdded(std::vector<Path>& queue, size_t first, size_t last) = 0;
    virtual void beforePathRemoval(std::vector<Path>& queue, size_t first, size_t last) = 0;
};