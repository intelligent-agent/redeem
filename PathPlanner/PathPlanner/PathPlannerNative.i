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

%rename(PathPlannerNative) PathPlanner;

#define NUM_AXIS 4

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



class PathPlanner {
  
public:
  PathPlanner();
  void queueMove(float startPos[NUM_AXIS],float endPos[NUM_AXIS],float speed);
  
  void run();
  
  void runThread();
  void stopThread(bool join);
  
  void setMaxFeedrates(unsigned long rates[NUM_AXIS]);
  void setPrintAcceleration(unsigned long accel[NUM_AXIS]);
  void setTravelAcceleration(unsigned long accel[NUM_AXIS]);
  void setAxisStepsPerMM(unsigned long stepPerMM[NUM_AXIS]);
  void setMaxJerk(unsigned long maxJerk, unsigned long maxZJerk);
  void setMaximumExtruderStartFeedrate(unsigned long maxstartfeedrate);
  void waitUntilFinished();
  bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
  
  
  virtual ~PathPlanner();

};


