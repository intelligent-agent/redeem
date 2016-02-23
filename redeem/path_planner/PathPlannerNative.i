%module PathPlannerNative

%include "typemaps.i"
%include "std_string.i"
%include <std_vector.i>
%include <typemaps.i>
%include <stdint.i>
%include exception.i


%{
#include "PathPlanner.h"
#include "Delta.h"
%}

%include "config.h"

%rename(PathPlannerNative) PathPlanner;

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

%apply FLOAT_T *OUTPUT { FLOAT_T* offset };
%apply FLOAT_T *OUTPUT { FLOAT_T* X, FLOAT_T* Y , FLOAT_T* Z};
%apply FLOAT_T *OUTPUT { FLOAT_T* Az, FLOAT_T* Bz , FLOAT_T* Cz};


class Delta {
 public:
  Delta();
  ~Delta();
  void setMainDimensions(FLOAT_T Hez_in, FLOAT_T L_in, FLOAT_T r_in);
  void setEffectorOffset(FLOAT_T Ae_in, FLOAT_T Be_in, FLOAT_T Ce_in);
  void setRadialError(FLOAT_T A_radial_in, FLOAT_T B_radial_in, FLOAT_T C_radial_in);
  void setTangentError(FLOAT_T A_tangential_in, FLOAT_T B_tangential_in, FLOAT_T C_tangential_in);
  void recalculate();
  void inverse_kinematics(FLOAT_T X, FLOAT_T Y, FLOAT_T Z, FLOAT_T* Az, FLOAT_T* Bz, FLOAT_T* Cz);
  void forward_kinematics(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* X, FLOAT_T* Y, FLOAT_T* Z);
  void vertical_offset(FLOAT_T Az, FLOAT_T Bz, FLOAT_T Cz, FLOAT_T* offset);
};

class PathPlanner {
 public:
  Delta delta_bot;
  PathPlanner(unsigned int cacheSize);
  bool initPRU(const std::string& firmware_stepper, const std::string& firmware_endstops);
  bool queueSyncEvent(bool isBlocking = true);
  int waitUntilSyncEvent();
  void clearSyncEvent();
  void queueMove(std::vector<FLOAT_T> startPos, std::vector<FLOAT_T> endPos, 
		 FLOAT_T speed, FLOAT_T accel, 
		 bool cancelable, bool optimize, 
		 bool enable_soft_endstops, bool use_bed_matrix, 
		 bool use_backlash_compensation, int tool_axis, bool virgin);
  void runThread();
  void stopThread(bool join);
  void waitUntilFinished();
  void setPrintMoveBufferWait(int dt);
  void setMinBufferedMoveTime(int dt);
  void setMaxBufferedMoveTime(int dt);
  void setMaxSpeeds(std::vector<FLOAT_T> speeds);
  void setMinSpeeds(std::vector<FLOAT_T> speeds);
  void setAxisStepsPerMeter(std::vector<FLOAT_T> stepPerM);
  void setAcceleration(std::vector<FLOAT_T> accel);
  void setJerks(std::vector<FLOAT_T> jerks);
  void setSoftEndstopsMin(std::vector<FLOAT_T> stops);
  void setSoftEndstopsMax(std::vector<FLOAT_T> stops);
  void setBedCompensationMatrix(std::vector<FLOAT_T> matrix);
  void setMaxPathLength(FLOAT_T maxLength);
  void setAxisConfig(int axis);
  void setState(std::vector<FLOAT_T> set);
  void enableSlaves(bool enable);
  void addSlave(int master_in, int slave_in);
  void setBacklashCompensation(std::vector<FLOAT_T> set);
  void resetBacklash();
  std::vector<FLOAT_T> getState();
  void suspend();
  void resume();
  void reset();
  virtual ~PathPlanner();

};
