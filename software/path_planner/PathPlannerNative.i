%module PathPlannerNative


%include "typemaps.i"
%include "std_string.i"
%include <std_vector.i>
%include <std_map.i>
%include <typemaps.i>
%include <stdint.i>


%{
#include "PathPlanner.h"
%}

%include "config.h"

%rename(PathPlannerNative) PathPlanner;


// Grab a 4 element array as a Python 4-tuple
%typemap(in) float[4](float temp[4]) {   // temp[4] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,"ffff",temp,temp+1,temp+2,temp+3)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 4 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}

%typemap(in) unsigned long[4](unsigned long temp[4]) {   // temp[4] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,"kkkk",temp,temp+1,temp+2,temp+3)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 4 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}

// Grab a 3 element array as a Python 3-tuple
%typemap(in) float[3](float temp[3]) {   // temp[3] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,"fff",temp,temp+1,temp+2)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 3 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}

%typemap(in) unsigned long[3](unsigned long temp[3]) {   // temp[3] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,"kkk",temp,temp+1,temp+2)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 3 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}



class Extruder {
public:
  
  /**
   * @brief Set the maximum feedrate of the extruder
   * @details Set the maximum feedrate of the extruder in m/s
   *
   * @param rates The feedrate of the extruder
   */
  void setMaxFeedrate(float rate);
  
  /**
   * @brief Set the maximum speed at which the extruder can start
   * @details Set the maximum speed at which the extruder can start
   *
   * @param maxstartfeedrate the maximum speed at which the extruder can start in m/s
   */
  void setMaxStartFeedrate(float maxstartfeedrate);
  
  /**
   * @brief Set the number of steps required to move each axis by 1 meter
   * @details Set the number of steps required to move each axis by 1 meter
   *
   * @param stepPerM the number of steps required to move each axis by 1 meter, consisting of a 3 length array.
   */
  void setAxisStepsPerMeter(unsigned long stepPerM);
  
  /**
   * @brief Set the max acceleration for printing moves
   * @details Set the max acceleration for moves when the extruder is activated
   *
   * @param accel The acceleration in m/s^2
   */
  void setPrintAcceleration(float accel);
  
  /**
   * @brief Set the max acceleration for travel moves
   * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
   *
   * @param accel The acceleration in m/s^2
   */
  void setTravelAcceleration(float accel);
  
  /**
   * @brief Return the bit that needs to be tiggled for setting direction and step pin of the stepper driver for this extruder
   * @return the bit that needs to be tiggled for setting direction and step pin of the stepper driver for this extruder
   *
   */
  unsigned int getStepperCommandPosition();
};



class PathPlanner {
  
public:
  /**
   * @brief Create a new path planner that is used to compute paths parameters and send it to the PRU for execution
   * @details Create a new path planner that is used to compute paths parameters and send it to the PRU for execution
   */
  PathPlanner();
  
  /**
   * @brief  Init the internal PRU co-processors
   * @details Init the internal PRU co-processors with the provided firmware
   * 
   * @param firmware_stepper The firmware for the stepper step generation, will be executed on PRU0
   * @param firmware_endstops The firmware for the endstop checks, will be executed on PRU1
   * 
   * @return true in case of success, false otherwise.
   */
  bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops) {
    return pru.initPRU(firmware_stepper, firmware_endstops);
  }

  /**
   * @brief Queue a line move for execution
   * @details Queue a line move execution in the path planner. Note that the path planner 
   * has no internal state in term of printer head position. Therefore you have 
   * to pass the correct start and end position everytime.
   * 
   * The coordinates unit is in meters. As a general rule, every public method of this class use SI units.
   * 
   * @param startPos The starting position of the path in meters
   * @param  endPose The end position of the path in meters
   * @param speed The feedrate (aka speed) of the move in m/s
   */
  void queueMove(float startPos[NUM_AXIS], float endPos[NUM_AXIS], float speed, bool cancelable, bool optimize);

  
  /**
   * @brief Run the path planner thread
   * @details Run the path planner thread that is in charge to compute the different delays and submit it to the PRU for execution.
   */
  void runThread();

  /**
   * @brief Stop the path planner thread
   * @details Stop the path planner thread and optionnaly wait until it is stopped before returning.
   * 
   * @param join If true, the method does not return until the thread is effectively stopped.
   */
  void stopThread(bool join);
  

  /**
   * @brief Wait until all queued move are finished to be executed
   * @details Wait until all queued move are finished to be executed
   */
  void waitUntilFinished();

  /**
   * @brief Set the maximum feedrates of the different axis
   * @details Set the maximum feedrates of the different axis in m/s
   * 
   * @param rates The feedrate for each of the axis, consisting of a 3 length array.
   */
  void setMaxFeedrates(float rates[3]);

  /**
   * @brief Set extruder number used
   * @details Set extruder number used starting with ext 0
   * 
   * @param extNr The extruder number
   */
  void setExtruder(int extNr);

  /**
   * @brief Return the extruder extNr
   * @details Return the extruder extNr in order to configure it.
   * @warning You have to call setExtruder() again if you modify the currently used extruder.
   * @param extNr The extruder number to get
   * @return The extruder corresponding to extNr
   */
  Extruder& getExtruder(int extNr);

  /**
   * @brief Set the number of steps required to move each axis by 1 meter
   * @details Set the number of steps required to move each axis by 1 meter
   * 
   * @param stepPerM the number of steps required to move each axis by 1 meter, consisting of a 3 length array.
   */
  void setAxisStepsPerMeter(unsigned long stepPerM[3]);

  /**
   * @brief Set the max acceleration for printing moves
   * @details Set the max acceleration for moves when the extruder is activated
   * 
   * @param accel The acceleration in m/s^2
   */
  void setPrintAcceleration(float accel[3]);

  /**
   * @brief Set the max acceleration for travel moves
   * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
   * 
   * @param accel The acceleration in m/s^2
   */
  void setTravelAcceleration(float accel[3]);

  /**
   * @brief Set the maximum speed that can be used when in a corner
   * @details The jerk determines your start speed and the maximum speed at the join of two segments.
   * 
   * Its unit is m/s. 
   * 
   * If the printer is standing still, the start speed is jerk/2. At the join of two segments, the speed 
   * difference is limited to the jerk value.
   * 
   * Examples:
   * 
   * For all examples jerk is assumed as 40.
   * 
   * Segment 1: vx = 50, vy = 0
   * Segment 2: vx = 0, vy = 50
   * v_diff = sqrt((50-0)^2+(0-50)^2) = 70.71
   * v_diff > jerk => vx_1 = vy_2 = jerk/v_diff*vx_1 = 40/70.71*50 = 28.3 mm/s at the join
   * 
   * Segment 1: vx = 50, vy = 0
   * Segment 2: vx = 35.36, vy = 35.36
   * v_diff = sqrt((50-35.36)^2+(0-35.36)^2) = 38.27 < jerk
   * Corner can be printed with full speed of 50 mm/s
   *
   * @param maxJerk The maximum jerk for X and Y axis in m/s
   * @param maxZJerk The maximum jerk for Z axis in m/s
   */
  void setMaxJerk(float maxJerk, float maxZJerk);

  void suspend();
  
  void resume();

  void reset();
  
  virtual ~PathPlanner();

};


