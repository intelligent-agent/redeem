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
	void setMaxFeedrate(FLOAT_T rate);

	void setMaxStartFeedrate(FLOAT_T maxstartfeedrate);

	void setAxisStepsPerMeter(unsigned long stepPerM);

	void setPrintAcceleration(FLOAT_T accel);

	void setTravelAcceleration(FLOAT_T accel);

	unsigned int getStepperCommandPosition();

	void setStepperCommandPosition(unsigned int pose);

	void setDirectionInverted(bool inverted);
};

class PathPlanner {
public:

	PathPlanner(unsigned int cacheSize);

	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);

	bool queueSyncEvent(bool isBlocking = true);

  int waitUntilSyncEvent();

  void clearSyncEvent();

  void queueMove(FLOAT_T startPos[NUM_AXIS], FLOAT_T endPos[NUM_AXIS], FLOAT_T speed, bool cancelable, bool optimize);

	void queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T speed, bool cancelable, bool optimize);

  void runThread();

  void stopThread(bool join);

  void waitUntilFinished();

  void setExtruder(int extNr);

  Extruder& getExtruder(int extNr);

	void setPrintMoveBufferWait(int dt);

	void setMinBufferedMoveTime(int dt);

	void setMaxBufferedMoveTime(int dt);

	void setMaxFeedrates(FLOAT_T rates[NUM_MOVING_AXIS]);

	void setAxisStepsPerMeter(unsigned long stepPerM[NUM_MOVING_AXIS]);

	void setPrintAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]);

	void setTravelAcceleration(FLOAT_T accel[NUM_MOVING_AXIS]);

  void setMaxJerk(FLOAT_T maxJerk, FLOAT_T maxZJerk);

  void suspend();
  
  void resume();

   void setDriveSystem(int driveSystem);

  void reset();
  
  virtual ~PathPlanner();

};


