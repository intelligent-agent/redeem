/*
 This file is part of Redeem - 3D Printer control software
 
 Author: Mathieu Monney
 Website: http://www.xwaves.net
 License: GNU GPLv3 http://www.gnu.org/copyleft/gpl.html
 
 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
 
 */

#include <iostream>
#include "PathPlanner.h"
#include "AlarmCallback.h"

class MyAlarmCallback: public AlarmCallback{
    public:
        void call(int alarmType, std::string message, std::string shortMessage){}
        ~MyAlarmCallback(){}

};

int main(int argc, const char * argv[])
{
	LOG( "Start test program" << std::endl);
	
    
    
    auto callback = MyAlarmCallback();
	PathPlanner planner(1024, callback);
	Path *prev=NULL;
	
	planner.initPRU("/tmp/firmware_runtime.bin","/tmp/firmware_endstops.bin");
	
	
	
	
	FLOAT_T start[5],end[5];
	
	bzero(start,5*4);
	bzero(end,5*4);
	
	planner.runThread();
		
    auto axisStepsPerM = VectorN();
	axisStepsPerM.values[0]=50*1000;
	axisStepsPerM.values[1]=50*1000;
	axisStepsPerM.values[2]=2133*1000;
	axisStepsPerM.values[3]=2133*1000;
	axisStepsPerM.values[4]=2133*1000;
	axisStepsPerM.values[5]=2133*1000;
	axisStepsPerM.values[6]=2133*1000;
	axisStepsPerM.values[7]=2133*1000;
	
    auto axisSpeedJumps = VectorN();
	axisSpeedJumps.values[0]=0.1;
	axisSpeedJumps.values[1]=0.1;
	axisSpeedJumps.values[2]=0.1;
	axisSpeedJumps.values[3]=0.1;
	axisSpeedJumps.values[4]=0.1;
	axisSpeedJumps.values[5]=0.1;
	axisSpeedJumps.values[6]=0.1;
	axisSpeedJumps.values[7]=0.1;

    planner.setMaxSpeedJumps(axisSpeedJumps);

	auto maxAccelerationMPerSquareSecond = VectorN();
	
	maxAccelerationMPerSquareSecond.values[0]=0.05;
	maxAccelerationMPerSquareSecond.values[1]=0.05;
	maxAccelerationMPerSquareSecond.values[2]=0.05;
		
	auto v = VectorN();
    v.values[0] = 2000.0;
    v.values[1] = 2000.0;
    v.values[2] = 2000.0;

	planner.setMaxSpeeds(v);
	planner.setAxisStepsPerMeter(axisStepsPerM);
	planner.setAcceleration(maxAccelerationMPerSquareSecond);
	

    auto axisSpeedJumps2 = VectorN();
	axisSpeedJumps2.values[0]=0;
	axisSpeedJumps2.values[1]=0;
	axisSpeedJumps2.values[2]=0;
	/*axisSpeedJumps2.values[3]=0;
	axisSpeedJumps2.values[4]=1;
	axisSpeedJumps2.values[5]=1;
	axisSpeedJumps2.values[6]=1;
	axisSpeedJumps2.values[7]=1;*/


    planner.setState(axisSpeedJumps2);

    planner.setAxisConfig(3);
    planner.delta_bot.setMainDimensions(1.0, 0.1);
    //    self.native_planner.delta_bot.setRadialError(Delta.A_radial, Delta.B_radial, Delta.C_radial)
    //self.native_planner.delta_bot.setAngularError(Delta.A_angular, Delta.B_angular, Delta.C_angular)

	for(int i=1;i<16;i++) {
        auto endWorldPos = VectorN();
        endWorldPos.values[0] = 0.00001*i;
        endWorldPos.values[1] = 0.00002*i;
        endWorldPos.values[2] = 0.00003*i;

	    FLOAT_T speed = 0.1;
        FLOAT_T accel = 0.05; 
	    bool cancelable = false;
        bool optimize = true; 
	    bool enable_soft_endstops = false;
        bool use_bed_matrix = false; 
	    bool use_backlash_compensation = false;
        bool is_probe = false;
	    int tool_axis = 0;

		planner.queueMove(endWorldPos, speed,
            accel,
	        cancelable,
            optimize,
	        enable_soft_endstops,
            use_bed_matrix,
	        use_backlash_compensation,
            is_probe,
	        tool_axis);
		
	}
	
	std::this_thread::sleep_for( std::chrono::milliseconds(2000) );

	planner.waitUntilFinished();
	
	planner.stopThread(true);
	
    return 0;
}

