#pragma once

#include "PathOptimizerInterface.h"

class PathOptimizer final : public PathOptimizerInterface
{
public:
    void beforePathRemoval(std::vector<Path>& queue, size_t first, size_t last) override;
    void onPathAdded(std::vector<Path>& queue, size_t first, size_t last) override;
};