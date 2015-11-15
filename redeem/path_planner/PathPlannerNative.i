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
#define FTL "d"
#elif FLOAT_T == float
#define FTL "f"
#else
#error Unsupported float type
#endif

// Grab a 8 element array as a Python 8-tuple
%typemap(in) FLOAT_T[8](FLOAT_T temp[8]) {   // temp[8] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,""FTL""FTL""FTL""FTL""FTL""FTL""FTL""FTL,temp,temp+1,temp+2,temp+3,temp+4,temp+5,temp+6,temp+7)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 8 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}
// Grab a 5 element array as a Python 5-tuple
%typemap(in) FLOAT_T[5](FLOAT_T temp[5]) {   // temp[5] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,""FTL""FTL""FTL""FTL""FTL,temp,temp+1,temp+2,temp+3,temp+4)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 5 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}

%typemap(in) unsigned long[5](unsigned long temp[5]) {   // temp[4] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,"kkkkk",temp,temp+1,temp+2,temp+3,temp+4)) {
      PyErr_SetString(PyExc_TypeError,"tuple must have 5 elements");
      return NULL;
    }
    $1 = &temp[0];
  } else {
    PyErr_SetString(PyExc_TypeError,"expected a tuple.");
    return NULL;
  }
}
// Grab a 4 element array as a Python 4-tuple
%typemap(in) FLOAT_T[4](FLOAT_T temp[4]) {   // temp[4] becomes a local variable
  if (PyTuple_Check($input)) {
    if (!PyArg_ParseTuple($input,""FTL""FTL""FTL""FTL,temp,temp+1,temp+2,temp+3)) {
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
    if (!PyArg_ParseTuple($input,""FTL""FTL""FTL,temp,temp+1,temp+2)) {
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

class PathPlanner {
public:
	PathPlanner(unsigned int cacheSize);
	bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
	bool queueSyncEvent(bool isBlocking = true);
    int waitUntilSyncEvent();
    void clearSyncEvent();
    void queueMove(FLOAT_T startPos[NUM_AXES], FLOAT_T endPos[NUM_AXES], FLOAT_T speed, FLOAT_T accel, bool cancelable, bool optimize);
	void queueBatchMove(FLOAT_T* batchData, int batchSize, FLOAT_T speed, FLOAT_T accel, bool cancelable, bool optimize);
    void runThread();
    void stopThread(bool join);
    void waitUntilFinished();
	void setPrintMoveBufferWait(int dt);
	void setMinBufferedMoveTime(int dt);
	void setMaxBufferedMoveTime(int dt);
	void setMaxSpeeds(FLOAT_T speeds[NUM_AXES]);
	void setMinSpeeds(FLOAT_T speeds[NUM_AXES]);
	void setAxisStepsPerMeter(FLOAT_T stepPerM[NUM_AXES]);
	void setAcceleration(FLOAT_T accel[NUM_AXES]);
	void setJerks(FLOAT_T jerks[NUM_AXES]);
    void suspend();
    void resume();
    void reset();
    virtual ~PathPlanner();

};


