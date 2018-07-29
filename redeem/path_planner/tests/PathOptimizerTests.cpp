#define _SILENCE_TR1_NAMESPACE_DEPRECATION_WARNING

#include "gtest/gtest.h"

#include <numeric>

#include "PathOptimizer.h"
#include "vector3.h"
#include "vectorN.h"

struct PathBuilder
{
    VectorN currentPosition;
    const VectorN stepsPerM;
    const VectorN maxSpeedJumps;
    const VectorN maxSpeeds;
    const VectorN maxAccelMPerSquareSecond;

    PathBuilder()
        : stepsPerM(10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000)
        , maxSpeedJumps(0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01)
        , maxSpeeds(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        , maxAccelMPerSquareSecond(0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1)
    {
    }

    Path makePath(double x, double y, double z, double speed)
    {
        Path result;

        VectorN travel(x, y, z, 0, 0, 0, 0, 0);

        VectorN endPosition = currentPosition + travel;

        result.initialize(
            (currentPosition * stepsPerM).round(), // machineStart
            (endPosition * stepsPerM).round(), // machineEnd
            currentPosition, // worldStart,
            endPosition, // worldEnd
            stepsPerM,
            maxSpeeds,
            maxAccelMPerSquareSecond,
            speed,
            std::numeric_limits<double>::infinity(),
            AXIS_CONFIG_XY,
            *(Delta*)nullptr,
            false,
            false);

        return result;
    }
};

struct PathOptimizerTests : ::testing::Test
{
    PathBuilder builder;
    PathOptimizer optimizer;
    std::vector<Path> paths;
    size_t pathsInUse = 0;

    PathOptimizerTests()
    {
        paths.resize(10);
        optimizer.setMaxSpeedJumps(builder.maxSpeedJumps);
    }

    void addPath(Path&& p)
    {
        paths[pathsInUse] = std::move(p);
        optimizer.onPathAdded(paths, 0, pathsInUse);
        pathsInUse++;
    }

    void run()
    {
        std::vector<Path> result;

        for (size_t i = 0; i < pathsInUse; i++)
        {
            optimizer.beforePathRemoval(paths, i, pathsInUse - 1);
        }
    }
};

TEST_F(PathOptimizerTests, OneMoveAtHalfMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.005));
    run();

    // This move should be full speed the whole time - maxSpeedJump[x] is 0.01 so we can just jump to full speed
    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, OneMoveAtMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.01));
    run();

    // This move can't jump to full speed - we only use half of maxSpeedJump when starting fresh or stopping completely.
    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, OneMoveAtLessThanMaxSpeedJump)
{
    addPath(builder.makePath(0.1, 0, 0, 0.001));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.001);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.001);
}

TEST_F(PathOptimizerTests, TwoMovesSameDirection)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMovesRightAngle)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0, 0.1, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005); // We can only use half of maxSpeedJump because we don't know what X was doing before this move
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.01); // We can use all of maxSpeedJump because we know the next move
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.01); // Same again - Y is jumping from 0 to 0.01
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005); // back to half because Y is jumping from 0.005 to <unknown>
}

/*
NOTE: These two tests cover behavior that is expected but not ideal.
The current notion of a single junction speed that's shared by two paths
means that the end speed of one path must be the start speed of the next
path, even if the rules of maximum speed jumps could potentially let us
do better.
*/

TEST_F(PathOptimizerTests, TwoMovesSlowingDown)
{
    addPath(builder.makePath(0.1, 0, 0, 0.03));
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.02); // Ideally this could be 0.03, but not today
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMovesSpeedingUp)
{
    addPath(builder.makePath(0.1, 0, 0, 0.02));
    addPath(builder.makePath(0.1, 0, 0, 0.03));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.02);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.02); // Ideally this could be 0.03, but not today
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), 0.005);
}

TEST_F(PathOptimizerTests, TwoMoves45DegreeAngle)
{
    addPath(builder.makePath(0.1, 0, 0, 0.01));
    addPath(builder.makePath(0.1, 0.1, 0, 0.01));
    run();

    EXPECT_DOUBLE_EQ(paths[0].getStartSpeed(), 0.005);
    EXPECT_DOUBLE_EQ(paths[0].getEndSpeed(), 0.01);
    EXPECT_DOUBLE_EQ(paths[1].getStartSpeed(), 0.01);
    EXPECT_DOUBLE_EQ(paths[1].getEndSpeed(), vabs(VectorN(0.005, 0.005, 0)));
}