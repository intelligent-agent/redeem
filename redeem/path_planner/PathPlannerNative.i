%module(directors="1") PathPlannerNative

%include "typemaps.i"
%include "std_string.i"
%include <std_vector.i>
%include <typemaps.i>
%include <stdint.i>
%include exception.i


%{
#include "PathPlanner.h"
#include "Delta.h"
#include "AlarmCallback.h"
%}

%include "config.h"

%rename(PathPlannerNative) PathPlanner;
%rename(AlarmCallbackNative) AlarmCallback;
%rename(SyncCallbackNative) SyncCallback;
%rename(WaitEventNative) WaitEvent;

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
  %template(vector_double) vector<double>;
}

%apply double *OUTPUT { double* offset };
%apply double *OUTPUT { double* X, double* Y , double* Z};
%apply double *OUTPUT { double* Az, double* Bz , double* Cz};

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

%feature("director") AlarmCallback;

class AlarmCallback
{
public:
  virtual void call(int alarmType, std::string message, std::string shortMessage);
  virtual ~AlarmCallback();
};



class Delta {
 public:
  Delta();
  ~Delta();
  void setMainDimensions(double L_in, double r_in);
  void setRadialError(double A_radial_in, double B_radial_in, double C_radial_in);
  void setAngularError(double A_angular_in, double B_angular_in, double C_angular_in);
  void worldToDelta(double X, double Y, double Z, double* Az, double* Bz, double* Cz);
  void deltaToWorld(double Az, double Bz, double Cz, double* X, double* Y, double* Z);
  void verticalOffset(double Az, double Bz, double Cz, double* offset);
};

%feature("director") SyncCallback;

class SyncCallback
{
public:
  virtual ~SyncCallback();
  virtual void syncComplete();
};

class WaitEvent
{
public:
  void signalWaitComplete();
};

class PathPlanner {
 public:
  Delta delta_bot;
  PathPlanner(unsigned int cacheSize, AlarmCallback& alarmCallback);
  bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
  void queueSyncEvent(SyncCallback& callback, bool isBlocking = true);
  %newobject queueWaitEvent;
  WaitEvent* queueWaitEvent();
  void queueMove(VectorN endPos, 
		 double speed, double accel, 
		 bool cancelable, bool optimize, 
		 bool enable_soft_endstops, bool use_bed_matrix, 
		 bool use_backlash_compensation, bool is_probe, int tool_axis);
  void runThread();
  void stopThread(bool join);
  void waitUntilFinished();
  void setMaxSpeeds(VectorN speeds);
  void setAxisStepsPerMeter(VectorN stepPerM);
  void setAcceleration(VectorN accel);
  void setMaxSpeedJumps(VectorN speedJumps);
  void setSoftEndstopsMin(VectorN stops);
  void setSoftEndstopsMax(VectorN stops);
  void setStopPrintOnSoftEndstopHit(bool stop);
  void setStopPrintOnPhysicalEndstopHit(bool stop);
  void setBedCompensationMatrix(std::vector<double> matrix);
  void setAxisConfig(int axis);
  void setState(VectorN set);
  void enableSlaves(bool enable);
  void addSlave(int master_in, int slave_in);
  void setBacklashCompensation(VectorN set);
  void resetBacklash();
  VectorN getState();
  bool getLastQueueMoveStatus();
  double getLastProbeDistance();
  void suspend();
  void resume();
  void reset();
  virtual ~PathPlanner();

};
