%module PathPlannerNative


%{
#define SWIG_FILE_WITH_INIT
%}
%include "numpy.i"
%init %{
import_array();
%}
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

#if FLOAT_T == double
#define FLOAT_TUPLE_LETTER "d"
#elif FLOAT_T == float
#define FLOAT_TUPLE_LETTER "f"
#else
#error Unsupported float type
#endif

// Grab a 4 element array as a Python 4-tuple
%typemap(in) FLOAT_T[4](FLOAT_T temp[4]) {   // temp[4] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,""FLOAT_TUPLE_LETTER""FLOAT_TUPLE_LETTER""FLOAT_TUPLE_LETTER""FLOAT_TUPLE_LETTER,temp,temp+1,temp+2,temp+3)) {
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
%typemap(in) FLOAT_T[3](FLOAT_T temp[3]) {   // temp[3] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,""FLOAT_TUPLE_LETTER""FLOAT_TUPLE_LETTER""FLOAT_TUPLE_LETTER,temp,temp+1,temp+2)) {
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

%apply (FLOAT_T* IN_ARRAY1, int DIM1 ) { (FLOAT_T* value, int othervalue) }
%apply (FLOAT_T* IN_ARRAY1, int DIM1 ) { (FLOAT_T* batchData, int batchSize) }
// %apply (int DIM1, FLOAT_T* IN_ARRAY1, FLOAT_T NONZERO, bool INPUT, bool INPUT) { (int batchSize, FLOAT_T* batchData, FLOAT_T speed, bool cancelable, bool optimize) }

class Extruder {
public:
  
  /**
   * @brief Set the maximum feedrate of the extruder
   * @details Set the maximum feedrate of the extruder in m/s
   *
   * @param rates The feedrate of the extruder
   */
  void setMaxFeedrate(FLOAT_T rate);
  
  /**
   * @brief Set the maximum speed at which the extruder can start
   * @details Set the maximum speed at which the extruder can start
   *
   * @param maxstartfeedrate the maximum speed at which the extruder can start in m/s
   */
  void setMaxStartFeedrate(FLOAT_T maxstartfeedrate);
  
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
  void setPrintAcceleration(FLOAT_T accel);
  
  /**
   * @brief Set the max acceleration for travel moves
   * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
   *
   * @param accel The acceleration in m/s^2
   */
  void setTravelAcceleration(FLOAT_T accel);
  
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
   * @brief Sets a syncronization point to be signaled by the PRU
   * @details Sets an option on the last queued move/segment to send a syncronization event when
   * encountered by the PRU
   *
   * @ param isBlocking Causes the PRU to suspend once the sync event occurs.
   * @ returns true if the sync event was successfully added.  False on failure.
   */                         
   bool queueSyncEvent(bool isBlocking);

  /**        
   * @brief Blocks until a pending Sync event is encountered.
   * @details Monitors the PRU for a sync event, then returns. Note that the event must be manually
   * cleared before processing can continue.
   *         
   */         
  void waitUntilSyncEvent();
                     
  /**      
   * @brief Clears a SINGLE sync event and restores normal operation of the stepper PRU
   * @details Clears the Sync event generated by the PRU then returns.
   * Note that a pending event must be manually cleared before processing can continue.
   *
   */                      
  void clearSyncEvent();

  /**                                                           
   * @brief Queue a line move for execution          
   * @details Queue a line move execution in the path planner. Note that the path planner
   * has no internal state in term of printer head position. Therefore you have
   * to pass the correct start and end position everytime.     
   *                                                        
   * The coordinates unit is in meters. As a general rule, every public method of this class use SI units.
   *
   * @param startPos The starting position of the path in meters
   * @param endPos The end position of the path in meters
   * @param speed The feedrate (aka speed) of the move in m/s
   * @param cancelable flags the move as cancelable.
   * @param optimize Wait for additional commands to fill the buffer, to optimize speed.
   */
  void queueMove(FLOAT_T startPos[NUM_AXIS], FLOAT_T endPos[NUM_AXIS], FLOAT_T speed, bool cancelable, bool optimize);


 /**
   * @brief Queue a batch of line moves for execution
   * @details Queue a batch of line moves for execution in the path planner. Note that the path planner
   * has no internal state in term of printer head position. Therefore you have
   * to pass the correct start and end position everytime.
   *         
   * The coordinates unit is in meters. As a general rule, every public method of this class use SI units.
   *       
   * @param numSegments number of line moves being queued
   * @param segments Block of FLOAT_T* line segments with startPos, endPos, and speed, for each segment
   * @param speed The feedrate (aka speed) of the move in m/s
   * @param cancelable flags the entire group of moves as cancelable.
   * @param optimize Waits upto PRINT_MOVE_BUFFER_WAIT to perform speed optimization on an entire group of moves.
   */          
  void queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T NONZERO, bool cancelable, bool optimize);
  
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
  void setMaxFeedrates(FLOAT_T rates[3]);

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
  void setPrintAcceleration(FLOAT_T accel[3]);

  /**
   * @brief Set the max acceleration for travel moves
   * @details Set the max acceleration for moves when the extruder is not activated (i.e. not printing)
   * 
   * @param accel The acceleration in m/s^2
   */
  void setTravelAcceleration(FLOAT_T accel[3]);

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
  void setMaxJerk(FLOAT_T maxJerk, FLOAT_T maxZJerk);

  void suspend();
  
  void resume();

  void reset();
  
  virtual ~PathPlanner();

};


