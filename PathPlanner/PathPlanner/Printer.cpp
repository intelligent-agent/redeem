//
//  Printer.cpp
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#include "Printer.h"
#include <cmath>
#include "Path.h"

/** \brief X, Y, Z max acceleration in mm/s^2 for printing moves or retracts. Make sure your printer can go that high!
 Overridden if EEPROM activated.
 */
#define MAX_ACCELERATION_UNITS_PER_SQ_SECOND_X 1000
#define MAX_ACCELERATION_UNITS_PER_SQ_SECOND_Y 1000
#define MAX_ACCELERATION_UNITS_PER_SQ_SECOND_Z 100

/** \brief X, Y, Z max acceleration in mm/s^2 for travel moves.  Overridden if EEPROM activated.*/
#define MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_X 2000
#define MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_Y 2000
#define MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_Z 100

#define XAXIS_STEPS_PER_MM 53
#define YAXIS_STEPS_PER_MM 53
#define ZAXIS_STEPS_PER_MM 1133

/** Maximum feedrate, the system allows. Higher feedrates are reduced to these values.
 The axis order in all axis related arrays is X, Y, Z
 Overridden if EEPROM activated.
 */
#define MAX_FEEDRATE_X 200
#define MAX_FEEDRATE_Y 200
#define MAX_FEEDRATE_Z 5

#define IGNORE_COORDINATE 99999

uint8_t Printer::unitIsInches = 0; ///< 0 = Units are mm, 1 = units are inches.
//Stepper Movement Variables
float Printer::axisStepsPerMM[4] = {XAXIS_STEPS_PER_MM,YAXIS_STEPS_PER_MM,ZAXIS_STEPS_PER_MM,1}; ///< Number of steps per mm needed.
float Printer::invAxisStepsPerMM[4]; ///< Inverse of axisStepsPerMM for faster conversion
float Printer::maxFeedrate[4] = {MAX_FEEDRATE_X, MAX_FEEDRATE_Y, MAX_FEEDRATE_Z}; ///< Maximum allowed feedrate.

#ifdef RAMP_ACCELERATION
//  float max_start_speed_units_per_second[4] = MAX_START_SPEED_UNITS_PER_SECOND; ///< Speed we can use, without acceleration.
float Printer::maxAccelerationMMPerSquareSecond[4] = {MAX_ACCELERATION_UNITS_PER_SQ_SECOND_X,MAX_ACCELERATION_UNITS_PER_SQ_SECOND_Y,MAX_ACCELERATION_UNITS_PER_SQ_SECOND_Z}; ///< X, Y, Z and E max acceleration in mm/s^2 for printing moves or retracts
float Printer::maxTravelAccelerationMMPerSquareSecond[4] = {MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_X,MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_Y,MAX_TRAVEL_ACCELERATION_UNITS_PER_SQ_SECOND_Z}; ///< X, Y, Z max acceleration in mm/s^2 for travel moves

/** Acceleration in steps/s^3 in printing mode.*/
unsigned long Printer::maxPrintAccelerationStepsPerSquareSecond[4];
/** Acceleration in steps/s^2 in movement mode.*/
unsigned long Printer::maxTravelAccelerationStepsPerSquareSecond[4];
#endif

signed char Printer::zBabystepsMissing = 0;
uint8_t Printer::relativeCoordinateMode = false;  ///< Determines absolute (false) or relative Coordinates (true).
uint8_t Printer::relativeExtruderCoordinateMode = false;  ///< Determines Absolute or Relative E Codes while in Absolute Coordinates mode. E is always relative in Relative Coordinates mode.

long Printer::currentPositionSteps[4];
float Printer::currentPosition[3];
float Printer::lastCmdPos[3];
long Printer::destinationSteps[4];
float Printer::coordinateOffset[3] = {0,0,0};
uint8_t Printer::flag0 = 0;
uint8_t Printer::flag1 = 0;
uint8_t Printer::debugLevel = 6; ///< Bitfield defining debug output. 1 = echo, 2 = info, 4 = error, 8 = dry run., 16 = Only communication, 32 = No moves
uint8_t Printer::stepsPerTimerCall = 1;
uint8_t Printer::menuMode = 0;


unsigned long Printer::interval;           ///< Last step duration in ticks.
unsigned long Printer::timer;              ///< used for acceleration/deceleration timing
unsigned long Printer::stepNumber;         ///< Step number in current move.

float Printer::minimumSpeed;               ///< lowest allowed speed to keep integration error small
float Printer::minimumZSpeed;
long Printer::xMaxSteps;                   ///< For software endstops, limit of move in positive direction.
long Printer::yMaxSteps;                   ///< For software endstops, limit of move in positive direction.
long Printer::zMaxSteps;                   ///< For software endstops, limit of move in positive direction.
long Printer::xMinSteps;                   ///< For software endstops, limit of move in negative direction.
long Printer::yMinSteps;                   ///< For software endstops, limit of move in negative direction.
long Printer::zMinSteps;                   ///< For software endstops, limit of move in negative direction.
float Printer::xLength;
float Printer::xMin;
float Printer::yLength;
float Printer::yMin;
float Printer::zLength;
float Printer::zMin;
float Printer::feedrate;                   ///< Last requested feedrate.
int Printer::feedrateMultiply;             ///< Multiplier for feedrate in percent (factor 1 = 100)
unsigned int Printer::extrudeMultiply;     ///< Flow multiplier in percdent (factor 1 = 100)
float Printer::maxJerk;                    ///< Maximum allowed jerk in mm/s
#if DRIVE_SYSTEM!=3
float Printer::maxZJerk;                   ///< Maximum allowed jerk in z direction in mm/s
#endif
float Printer::offsetX;                     ///< X-offset for different extruder positions.
float Printer::offsetY;                     ///< Y-offset for different extruder positions.
speed_t Printer::vMaxReached;         ///< Maximumu reached speed
unsigned long Printer::msecondsPrinting;            ///< Milliseconds of printing time (means time with heated extruder)
float Printer::filamentPrinted;            ///< mm of filament printed since counting started
uint8_t Printer::wasLastHalfstepping;         ///< Indicates if last move had halfstepping enabled
#if ENABLE_BACKLASH_COMPENSATION
float Printer::backlashX;
float Printer::backlashY;
float Printer::backlashZ;
uint8_t Printer::backlashDir;
#endif

float Printer::Extruder_maxStartFeedrate=10;

void Printer::moveToReal(float x,float y,float z,float e,float f)
{
    if(x == IGNORE_COORDINATE)
        x = currentPosition[X_AXIS];
    if(y == IGNORE_COORDINATE)
        y = currentPosition[Y_AXIS];
    if(z == IGNORE_COORDINATE)
        z = currentPosition[Z_AXIS];
    currentPosition[X_AXIS] = x;
    currentPosition[Y_AXIS] = y;
    currentPosition[Z_AXIS] = z;
#if FEATURE_AUTOLEVEL && FEATURE_Z_PROBE
    if(isAutolevelActive())
        transformToPrinter(x + Printer::offsetX,y + Printer::offsetY,z,x,y,z);
    else
#endif // FEATURE_AUTOLEVEL
    {
        x += Printer::offsetX;
        y += Printer::offsetY;
    }
    if(x != IGNORE_COORDINATE)
        destinationSteps[X_AXIS] = floor(x * axisStepsPerMM[X_AXIS] + 0.5);
    if(y != IGNORE_COORDINATE)
        destinationSteps[Y_AXIS] = floor(y * axisStepsPerMM[Y_AXIS] + 0.5);
    if(z != IGNORE_COORDINATE)
        destinationSteps[Z_AXIS] = floor(z * axisStepsPerMM[Z_AXIS] + 0.5);
    if(e != IGNORE_COORDINATE)
        destinationSteps[E_AXIS] = e * axisStepsPerMM[E_AXIS];
    if(f != IGNORE_COORDINATE)
        Printer::feedrate = f;
	

    PrintLine::queueCartesianMove(true,true);
}

bool Printer::isPositionAllowed(float x,float y,float z) {
    if(isNoDestinationCheck())  return true;
    bool allowed = true;
    if(!allowed) {
        Printer::updateCurrentPosition(true);
        //Commands::printCurrentPosition();
    }
    return allowed;
}


void Printer::updateCurrentPosition(bool copyLastCmd)
{
    currentPosition[X_AXIS] = (float)(currentPositionSteps[X_AXIS])*invAxisStepsPerMM[X_AXIS];
    currentPosition[Y_AXIS] = (float)(currentPositionSteps[Y_AXIS])*invAxisStepsPerMM[Y_AXIS];
    currentPosition[Z_AXIS] = (float)(currentPositionSteps[Z_AXIS])*invAxisStepsPerMM[Z_AXIS];
    currentPosition[X_AXIS] -= Printer::offsetX;
    currentPosition[Y_AXIS] -= Printer::offsetY;
    if(copyLastCmd) {
        lastCmdPos[X_AXIS] = currentPosition[X_AXIS];
        lastCmdPos[Y_AXIS] = currentPosition[Y_AXIS];
        lastCmdPos[Z_AXIS] = currentPosition[Z_AXIS];
    }
    //Com::printArrayFLN(Com::tP,currentPosition,3,4);
}


void Printer::constrainDestinationCoords()
{
    if(isNoDestinationCheck()) return;
#if min_software_endstop_x == true
    if (destinationSteps[X_AXIS] < xMinSteps) Printer::destinationSteps[X_AXIS] = Printer::xMinSteps;
#endif
#if min_software_endstop_y == true
    if (destinationSteps[Y_AXIS] < yMinSteps) Printer::destinationSteps[Y_AXIS] = Printer::yMinSteps;
#endif
#if min_software_endstop_z == true
    if (destinationSteps[Z_AXIS] < zMinSteps) Printer::destinationSteps[Z_AXIS] = Printer::zMinSteps;
#endif
	
#if max_software_endstop_x == true
    if (destinationSteps[X_AXIS] > Printer::xMaxSteps) Printer::destinationSteps[X_AXIS] = Printer::xMaxSteps;
#endif
#if max_software_endstop_y == true
    if (destinationSteps[Y_AXIS] > Printer::yMaxSteps) Printer::destinationSteps[Y_AXIS] = Printer::yMaxSteps;
#endif
#if max_software_endstop_z == true
    if (destinationSteps[Z_AXIS] > Printer::zMaxSteps) Printer::destinationSteps[Z_AXIS] = Printer::zMaxSteps;
#endif
}
