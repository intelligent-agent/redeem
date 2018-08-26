#pragma once

// first we have to include everything PathPlanner includes

#include "../Logger.h"
#include <assert.h>
#include <atomic>
#include <iostream>
#include <mutex>
#include <string.h>
#include <strings.h>
#include <thread>
#include <vector>

// and now we do terrible things to PathPlanner...
#define private public
#include "../PathPlanner.h"
#undef private

#include "../Path.h"

struct RenderedPath
{
    Path path;
    std::vector<SteppersCommand> stepperCommands;
};

class PruDump
{
private:
    static PruDump* singleton;

    friend class PruTimer;

    std::vector<RenderedPath> renderedPaths;

public:
    static PruDump* get();
    void test(PathPlanner& pathPlanner);
    void dumpPath(const RenderedPath& path);
};
