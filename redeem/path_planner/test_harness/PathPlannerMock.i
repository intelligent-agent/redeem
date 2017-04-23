%module PathPlannerMock

%include "typemaps.i"
%include "std_string.i"
%include <std_vector.i>
%include <typemaps.i>
%include <stdint.i>
%include exception.i


%{
#include "../PathPlanner.h"
#include "../Delta.h"
#include "PruDump.h"
%}

%include "../config.h"

%rename(PathPlannerMock) PathPlanner;

// exception handler
%exception {
  try {
  $action
  }
  catch (InputSizeError) {
    PyErr_SetString(PyExc_RuntimeError,"Input size does not match required value, see path_planner/config.h");
    return 0;
  }
}

// Instantiate template for vector<>
namespace std {
  %template(vector_FLOAT_T) vector<FLOAT_T>;
}


%typemap(in) VectorN {
  if (!PySequence_Check($input)) {
      PyErr_SetString(PyExc_TypeError,"Expecting a sequence");
      return NULL;
  }
  if (PyObject_Length($input) != NUM_AXES) {
      PyErr_SetString(PyExc_ValueError,"Expecting a sequence with NUM_AXES elements");
      return NULL;
  }
  for (int i = 0; i < NUM_AXES; i++) {
    PyObject *o = PySequence_GetItem($input,i);
    if (PyFloat_Check(o)) {
      $1.values[i] = PyFloat_AsDouble(o);
    }
    else if(PyLong_Check(o)) {
      $1.values[i] = PyLong_AsDouble(o);
    }
    else if(PyInt_Check(o)) {
      $1.values[i] = (double)PyInt_AsLong(o);
    }
    else {
      Py_XDECREF(o);
      PyErr_SetString(PyExc_ValueError,"Expecting a sequence of floats or longs");
      return NULL;
    }
    
    Py_DECREF(o);
  }
}

%typemap(out) VectorN (PyObject* list, PyObject* element) {
  list = PyList_New(NUM_AXES);
  
  if(!PyList_Check(list)) {
    Py_XDECREF(list);
    PyErr_SetString(PyExc_RuntimeError, "Failed to allocate List for VectorN");
    return NULL;
  }
  
  for(int i = 0; i < NUM_AXES; i++) {
    element = PyFloat_FromDouble($1.values[i]);

    if(!PyFloat_Check(element)) {
      Py_XDECREF(element);
      PyErr_SetString(PyExc_RuntimeError, "Failed to allocate PyFloat for VectorN");
      Py_DECREF(list);
      return NULL;
    }

    if(-1 == PyList_SetItem(list, i, element)) {
      PyErr_SetString(PyExc_RuntimeError, "Failed to insert PyFloat into PyList for VectorN");
      Py_DECREF(element);
      Py_DECREF(list);
      return NULL;
    }
  }
  
  $result = list;
}


%apply FLOAT_T *OUTPUT { FLOAT_T* offset };
%apply FLOAT_T *OUTPUT { FLOAT_T* X, FLOAT_T* Y , FLOAT_T* Z};
%apply FLOAT_T *OUTPUT { FLOAT_T* Az, FLOAT_T* Bz , FLOAT_T* Cz};


class Delta {
 public:
  Delta();
  ~Delta();
  void setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in);
  void setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in);
  void setAngularError(FLOAT_T A_angular_in, FLOAT_T B_angular_in, FLOAT_T C_angular_in);
  void worldToDelta(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz);
  void deltaToWorld(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z);
  void verticalOffset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset);
};

class PathPlanner {
 public:
  Delta delta_bot;
  PathPlanner(unsigned int cacheSize);
  bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
  bool queueSyncEvent(bool isBlocking = true);
  int waitUntilSyncEvent();
  void clearSyncEvent();
  void queueMove(VectorN startPos, VectorN endPos, 
		 FLOAT_T speed, FLOAT_T accel, 
		 bool cancelable, bool optimize, 
		 bool enable_soft_endstops, bool use_bed_matrix, 
		 bool use_backlash_compensation, int tool_axis, bool virgin);
  void runThread();
  void stopThread(bool join);
  void waitUntilFinished();
  void setPrintMoveBufferWait(int dt);
  void setMaxBufferedMoveTime(long long dt);
  void setMaxSpeeds(VectorN speeds);
  void setMinSpeeds(VectorN speeds);
  void setAxisStepsPerMeter(VectorN stepPerM);
  void setAcceleration(VectorN accel);
  void setJerks(VectorN jerks);
  void setSoftEndstopsMin(VectorN stops);
  void setSoftEndstopsMax(VectorN stops);
  void setBedCompensationMatrix(std::vector<FLOAT_T> matrix);
  void setMaxPathLength(FLOAT_T maxLength);
  void setAxisConfig(int axis);
  void setState(VectorN set);
  void enableSlaves(bool enable);
  void addSlave(int master_in, int slave_in);
  void setBacklashCompensation(VectorN set);
  void resetBacklash();
  VectorN getState();
  void suspend();
  void resume();
  void reset();
  virtual ~PathPlanner();

};

class PruDump {
 public:
  static PruDump* get();
  void test(PathPlanner& pathPlanner);
};
