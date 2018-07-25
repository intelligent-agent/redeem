#pragma once

#include "PathOptimizerInterface.h"

class PathOptimizer final : public PathOptimizerInterface
{
public:
    PathOptimizer(size_t queueSize)
    {
    }

    void optimizeForward(std::vector<Path>& queue, size_t first, size_t last) override;
    void optimizeBackward(std::vector<Path>& queue, size_t first, size_t last) override;
};