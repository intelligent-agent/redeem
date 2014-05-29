//
//  Printer.h
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef __PathPlanner__Printer__
#define __PathPlanner__Printer__

#include <iostream>

typedef uint32_t speed_t;
typedef uint32_t ticks_t;
typedef uint32_t millis_t;
typedef uint32_t flag8_t;

#define RAMP_ACCELERATION 1

#define PRINTER_FLAG0_STEPPER_DISABLED      1
#define PRINTER_FLAG0_SEPERATE_EXTRUDER_INT 2
#define PRINTER_FLAG0_TEMPSENSOR_DEFECT     4
#define PRINTER_FLAG0_FORCE_CHECKSUM        8
#define PRINTER_FLAG0_MANUAL_MOVE_MODE      16
#define PRINTER_FLAG0_AUTOLEVEL_ACTIVE      32
#define PRINTER_FLAG0_ZPROBEING             64
#define PRINTER_FLAG0_LARGE_MACHINE         128
#define PRINTER_FLAG1_HOMED                 1
#define PRINTER_FLAG1_AUTOMOUNT             2
#define PRINTER_FLAG1_ANIMATION             4
#define PRINTER_FLAG1_ALLKILLED             8
#define PRINTER_FLAG1_UI_ERROR_MESSAGE      16
#define PRINTER_FLAG1_NO_DESTINATION_CHECK  32
#define ANALYZER_ON(x)
#define WRITE(pin,state)
#define ANALYZER_OFF(x)

#define X_AXIS 0
#define Y_AXIS 1
#define Z_AXIS 2
#define E_AXIS 3

#define STEP_DOUBLER_FREQUENCY 0xFFFFFFFF

class Printer {
public:
public:
    static uint8_t menuMode;
    static float axisStepsPerMM[];
    static float invAxisStepsPerMM[];
    static float maxFeedrate[];
    static float maxAccelerationMMPerSquareSecond[];
    static float maxTravelAccelerationMMPerSquareSecond[];
    static unsigned long maxPrintAccelerationStepsPerSquareSecond[];
    static unsigned long maxTravelAccelerationStepsPerSquareSecond[];
    static uint8_t relativeCoordinateMode;    ///< Determines absolute (false) or relative Coordinates (true).
    static uint8_t relativeExtruderCoordinateMode;  ///< Determines Absolute or Relative E Codes while in Absolute Coordinates mode. E is always relative in Relative Coordinates mode.
	
    static uint8_t unitIsInches;
	
    static uint8_t debugLevel;
    static uint8_t flag0,flag1; // 1 = stepper disabled, 2 = use external extruder interrupt, 4 = temp Sensor defect, 8 = homed
    static uint8_t stepsPerTimerCall;
    static unsigned long interval;    ///< Last step duration in ticks.
    static unsigned long timer;              ///< used for acceleration/deceleration timing
    static unsigned long stepNumber;         ///< Step number in current move.
    static float coordinateOffset[3];
    static long currentPositionSteps[4];     ///< Position in steps from origin.
    static float currentPosition[3];
    static float lastCmdPos[3]; ///< Last coordinates send by gcodes
    static long destinationSteps[4];         ///< Target position in steps.

    static signed char zBabystepsMissing;
    static float minimumSpeed;               ///< lowest allowed speed to keep integration error small
    static float minimumZSpeed;              ///< lowest allowed speed to keep integration error small
    static long xMaxSteps;                   ///< For software endstops, limit of move in positive direction.
    static long yMaxSteps;                   ///< For software endstops, limit of move in positive direction.
    static long zMaxSteps;                   ///< For software endstops, limit of move in positive direction.
    static long xMinSteps;                   ///< For software endstops, limit of move in negative direction.
    static long yMinSteps;                   ///< For software endstops, limit of move in negative direction.
    static long zMinSteps;                   ///< For software endstops, limit of move in negative direction.
    static float xLength;
    static float xMin;
    static float yLength;
    static float yMin;
    static float zLength;
    static float zMin;
    static float feedrate;                   ///< Last requested feedrate.
    static int feedrateMultiply;             ///< Multiplier for feedrate in percent (factor 1 = 100)
    static unsigned int extrudeMultiply;     ///< Flow multiplier in percdent (factor 1 = 100)
    static float maxJerk;                    ///< Maximum allowed jerk in mm/s
    static float maxZJerk;                   ///< Maximum allowed jerk in z direction in mm/s
    static float offsetX;                     ///< X-offset for different extruder positions.
    static float offsetY;                     ///< Y-offset for different extruder positions.
    static speed_t vMaxReached;         ///< Maximumu reached speed
    static unsigned long msecondsPrinting;            ///< Milliseconds of printing time (means time with heated extruder)
    static float filamentPrinted;            ///< mm of filament printed since counting started
    static uint8_t wasLastHalfstepping;         ///< Indicates if last move had halfstepping enabled
#if ENABLE_BACKLASH_COMPENSATION
    static float backlashX;
    static float backlashY;
    static float backlashZ;
    static uint8_t backlashDir;
#endif
#ifdef DEBUG_STEPCOUNT
    static long totalStepsRemaining;
#endif
#ifdef DEBUG_SEGMENT_LENGTH
    static float maxRealSegmentLength;
#endif
#ifdef DEBUG_REAL_JERK
    static float maxRealJerk;
#endif
    static inline void setMenuMode(uint8_t mode,bool on) {
        if(on)
            menuMode |= mode;
        else
            menuMode &= ~mode;
    }
    static inline bool isMenuMode(uint8_t mode) {
        return (menuMode & mode)==mode;
    }
    static inline bool debugEcho()
    {
        return ((debugLevel & 1)!=0);
    }
    static inline bool debugInfo()
    {
        return ((debugLevel & 2)!=0);
    }
    static inline bool debugErrors()
    {
        return ((debugLevel & 4)!=0);
    }
    static inline bool debugDryrun()
    {
        return ((debugLevel & 8)!=0);
    }
    static inline bool debugCommunication()
    {
        return ((debugLevel & 16)!=0);
    }
    static inline bool debugNoMoves() {
        return ((debugLevel & 32)!=0);
    }
	
    static inline uint8_t isLargeMachine()
    {
        return flag0 & PRINTER_FLAG0_LARGE_MACHINE;
    }
    static inline void setLargeMachine(uint8_t b)
    {
        flag0 = (b ? flag0 | PRINTER_FLAG0_LARGE_MACHINE : flag0 & ~PRINTER_FLAG0_LARGE_MACHINE);
    }
    static inline uint8_t isAdvanceActivated()
    {
        return flag0 & PRINTER_FLAG0_SEPERATE_EXTRUDER_INT;
    }
    static inline void setAdvanceActivated(uint8_t b)
    {
        flag0 = (b ? flag0 | PRINTER_FLAG0_SEPERATE_EXTRUDER_INT : flag0 & ~PRINTER_FLAG0_SEPERATE_EXTRUDER_INT);
    }
    static inline uint8_t isHomed()
    {
        return flag1 & PRINTER_FLAG1_HOMED;
    }
    static inline void setHomed(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_HOMED : flag1 & ~PRINTER_FLAG1_HOMED);
    }
    static inline uint8_t isAllKilled()
    {
        return flag1 & PRINTER_FLAG1_ALLKILLED;
    }
    static inline void setAllKilled(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_ALLKILLED : flag1 & ~PRINTER_FLAG1_ALLKILLED);
    }
    static inline uint8_t isAutomount()
    {
        return flag1 & PRINTER_FLAG1_AUTOMOUNT;
    }
    static inline void setAutomount(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_AUTOMOUNT : flag1 & ~PRINTER_FLAG1_AUTOMOUNT);
    }
    static inline uint8_t isAnimation()
    {
        return flag1 & PRINTER_FLAG1_ANIMATION;
    }
    static inline void setAnimation(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_ANIMATION : flag1 & ~PRINTER_FLAG1_ANIMATION);
    }
    static inline uint8_t isUIErrorMessage()
    {
        return flag1 & PRINTER_FLAG1_UI_ERROR_MESSAGE;
    }
    static inline void setUIErrorMessage(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_UI_ERROR_MESSAGE : flag1 & ~PRINTER_FLAG1_UI_ERROR_MESSAGE);
    }
    static inline uint8_t isNoDestinationCheck()
    {
        return flag1 & PRINTER_FLAG1_NO_DESTINATION_CHECK;
    }
    static inline void setNoDestinationCheck(uint8_t b)
    {
        flag1 = (b ? flag1 | PRINTER_FLAG1_NO_DESTINATION_CHECK : flag1 & ~PRINTER_FLAG1_NO_DESTINATION_CHECK);
    }
    static inline void toggleAnimation() {
        setAnimation(!isAnimation());
    }
    static inline float convertToMM(float x)
    {
        return (unitIsInches ? x*25.4 : x);
    }
    static inline bool isXMinEndstopHit()
    {
#if X_MIN_PIN>-1 && MIN_HARDWARE_ENDSTOP_X
        return READ(X_MIN_PIN) != ENDSTOP_X_MIN_INVERTING;
#else
        return false;
#endif
    }
    static inline bool isYMinEndstopHit()
    {
#if Y_MIN_PIN>-1 && MIN_HARDWARE_ENDSTOP_Y
        return READ(Y_MIN_PIN) != ENDSTOP_Y_MIN_INVERTING;
#else
        return false;
#endif
    }
    static inline bool isZMinEndstopHit()
    {
#if Z_MIN_PIN>-1 && MIN_HARDWARE_ENDSTOP_Z
        return READ(Z_MIN_PIN) != ENDSTOP_Z_MIN_INVERTING;
#else
        return false;
#endif
    }
    static inline bool isXMaxEndstopHit()
    {
#if X_MAX_PIN>-1 && MAX_HARDWARE_ENDSTOP_X
        return READ(X_MAX_PIN) != ENDSTOP_X_MAX_INVERTING;
#else
        return false;
#endif
    }
    static inline bool isYMaxEndstopHit()
    {
#if Y_MAX_PIN>-1 && MAX_HARDWARE_ENDSTOP_Y
        return READ(Y_MAX_PIN) != ENDSTOP_Y_MAX_INVERTING;
#else
        return false;
#endif
    }
    static inline bool isZMaxEndstopHit()
    {
#if Z_MAX_PIN>-1 && MAX_HARDWARE_ENDSTOP_Z
        return READ(Z_MAX_PIN) != ENDSTOP_Z_MAX_INVERTING;
#else
        return false;
#endif
    }
    static inline bool areAllSteppersDisabled()
    {
        return flag0 & PRINTER_FLAG0_STEPPER_DISABLED;
    }
    static inline void setAllSteppersDiabled()
    {
        flag0 |= PRINTER_FLAG0_STEPPER_DISABLED;
    }
    static inline void unsetAllSteppersDisabled()
    {
        flag0 &= ~PRINTER_FLAG0_STEPPER_DISABLED;
    }
    static inline bool isAnyTempsensorDefect()
    {
        return (flag0 & PRINTER_FLAG0_TEMPSENSOR_DEFECT);
    }
    static inline bool isManualMoveMode()
    {
        return (flag0 & PRINTER_FLAG0_MANUAL_MOVE_MODE);
    }
    static inline void setManualMoveMode(bool on)
    {
        flag0 = (on ? flag0 | PRINTER_FLAG0_MANUAL_MOVE_MODE : flag0 & ~PRINTER_FLAG0_MANUAL_MOVE_MODE);
    }
    static inline bool isAutolevelActive()
    {
        return (flag0 & PRINTER_FLAG0_AUTOLEVEL_ACTIVE)!=0;
    }
    static void setAutolevelActive(bool on);
    static inline void setZProbingActive(bool on)
    {
        flag0 = (on ? flag0 | PRINTER_FLAG0_ZPROBEING : flag0 & ~PRINTER_FLAG0_ZPROBEING);
    }
    static inline bool isZProbingActive()
    {
        return (flag0 & PRINTER_FLAG0_ZPROBEING);
    }
    static inline bool isZProbeHit()
    {
#if FEATURE_Z_PROBE
        return (Z_PROBE_ON_HIGH ? READ(Z_PROBE_PIN) : !READ(Z_PROBE_PIN));
#else
        return false;
#endif
    }
    static inline void executeXYGantrySteps()
    {
#if defined(XY_GANTRY)
        if(motorX <= -2)
        {
            ANALYZER_ON(ANALYZER_CH2);
            WRITE(X_STEP_PIN,HIGH);
#if FEATURE_TWO_XSTEPPER
            WRITE(X2_STEP_PIN,HIGH);
#endif
            motorX += 2;
        }
        else if(motorX >= 2)
        {
            ANALYZER_ON(ANALYZER_CH2);
            WRITE(X_STEP_PIN,HIGH);
#if FEATURE_TWO_XSTEPPER
            WRITE(X2_STEP_PIN,HIGH);
#endif
            motorX -= 2;
        }
        if(motorY <= -2)
        {
            ANALYZER_ON(ANALYZER_CH3);
            WRITE(Y_STEP_PIN,HIGH);
#if FEATURE_TWO_YSTEPPER
            WRITE(Y2_STEP_PIN,HIGH);
#endif
            motorY += 2;
        }
        else if(motorY >= 2)
        {
            ANALYZER_ON(ANALYZER_CH3);
            WRITE(Y_STEP_PIN,HIGH);
#if FEATURE_TWO_YSTEPPER
            WRITE(Y2_STEP_PIN,HIGH);
#endif
            motorY -= 2;
        }
#endif
    }
    static inline void endXYZSteps()
    {
        WRITE(X_STEP_PIN,LOW);
        WRITE(Y_STEP_PIN,LOW);
        WRITE(Z_STEP_PIN,LOW);
#if FEATURE_TWO_XSTEPPER
        WRITE(X2_STEP_PIN,LOW);
#endif
#if FEATURE_TWO_YSTEPPER
        WRITE(Y2_STEP_PIN,LOW);
#endif
#if FEATURE_TWO_ZSTEPPER
        WRITE(Z2_STEP_PIN,LOW);
#endif
        ANALYZER_OFF(ANALYZER_CH1);
        ANALYZER_OFF(ANALYZER_CH2);
        ANALYZER_OFF(ANALYZER_CH3);
        ANALYZER_OFF(ANALYZER_CH6);
        ANALYZER_OFF(ANALYZER_CH7);
    }
    static inline speed_t updateStepsPerTimerCall(speed_t vbase)
    {
        if(vbase>STEP_DOUBLER_FREQUENCY)
        {
#if ALLOW_QUADSTEPPING
            if(vbase>STEP_DOUBLER_FREQUENCY*2)
            {
                Printer::stepsPerTimerCall = 4;
                return vbase>>2;
            }
            else
            {
                Printer::stepsPerTimerCall = 2;
                return vbase>>1;
            }
#else
            Printer::stepsPerTimerCall = 2;
            return vbase>>1;
#endif
        }
        else
        {
            Printer::stepsPerTimerCall = 1;
        }
        return vbase;
    }
    static inline void disableAllowedStepper()
    {

    }
    static inline float realXPosition()
    {
        return currentPosition[0];
    }
	
    static inline float realYPosition()
    {
        return currentPosition[1];
    }
	
    static inline float realZPosition()
    {
        return currentPosition[2];
    }
    static inline void realPosition(float &xp,float &yp,float &zp)
    {
        xp = currentPosition[X_AXIS];
        yp = currentPosition[Y_AXIS];
        zp = currentPosition[Z_AXIS];
    }
    static inline void insertStepperHighDelay() {
#if STEPPER_HIGH_DELAY>0
        HAL::delayMicroseconds(STEPPER_HIGH_DELAY);
#endif
    }
    static void constrainDestinationCoords();
    static void updateDerivedParameter();
    static void updateCurrentPosition(bool copyLastCmd = false);
    static void kill(uint8_t only_steppers);
    static void updateAdvanceFlags();
    static void setup();
    static void defaultLoopActions();
    //static uint8_t setDestinationStepsFromGCode(GCode *com);
    static void moveTo(float x,float y,float z,float e,float f);
    static void moveToReal(float x,float y,float z,float e,float f);
    static void homeAxis(bool xaxis,bool yaxis,bool zaxis); /// Home axis
    static void setOrigin(float xOff,float yOff,float zOff);
    static bool isPositionAllowed(float x,float y,float z);

    static void zBabystep();
	
	
	/*EXTRUDER*/
#warning fixme
	static float Extruder_maxStartFeedrate;
	
private:
    static void homeXAxis();
    static void homeYAxis();
    static void homeZAxis();
};

#endif /* defined(__PathPlanner__Printer__) */
