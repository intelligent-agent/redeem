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

int main(int argc, const char * argv[])
{
	LOG( "Start test program" << std::endl);
	

	PathPlanner planner;
	Path *prev=NULL;
	
	planner.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin");
	
	
	
	
	FLOAT_T start[5],end[5];
	
	bzero(start,5*4);
	bzero(end,5*4);
	
	planner.runThread();
	
	///*std::this_thread::sleep_for( std::chrono::milliseconds(2000) );
	/*
	
	for(int i=0;i<100;i++) {
		end[0] = i/1000.0;
		planner.queueMove(start,end,0.05,false);
		start[0] = end[0];
	}*/
	
	
	FLOAT_T maxFeedrate[3];
	
	maxFeedrate[0]=200; //m/s
	maxFeedrate[1]=200;
	maxFeedrate[2]=5;
	
	unsigned long axisStepsPerM[3];
	
	axisStepsPerM[0]=50*1000;
	axisStepsPerM[1]=50*1000;
	axisStepsPerM[2]=2133*1000;
	
	FLOAT_T maxAccelerationMPerSquareSecond[3];
	
	maxAccelerationMPerSquareSecond[0]=0.05;
	maxAccelerationMPerSquareSecond[1]=0.05;
	maxAccelerationMPerSquareSecond[2]=0.05;
	
	FLOAT_T maxTravelAccelerationMPerSquareSecond[3];
	
	maxTravelAccelerationMPerSquareSecond[0]=0.05;
	maxTravelAccelerationMPerSquareSecond[1]=0.05;
	maxTravelAccelerationMPerSquareSecond[2]=0.05;
	
	
	planner.setMaxFeedrates(maxFeedrate);
	planner.setAxisStepsPerMeter(axisStepsPerM);
	planner.setPrintAcceleration(maxAccelerationMPerSquareSecond);
	planner.setTravelAcceleration(maxTravelAccelerationMPerSquareSecond);
	
	
	Extruder & extruder = planner.getExtruder(0);
	
	extruder.setAxisStepsPerMeter(535*1000.0);
	extruder.setTravelAcceleration(0.05);
	extruder.setPrintAcceleration(0.05);
	extruder.setMaxFeedrate(0.2);
	extruder.setMaxStartFeedrate(20/1000.0);
	
	planner.setExtruder(0);

	/*G1 X20.5000620480408 Y19.1339750384809 F6000
	G1 X41.0000934550738 Y54.6409984607654 F6000
	G1 X62.000125628132 Y18.2679500769617 F6000*/
	
	FLOAT_T speed = 6000/60000.0;
	
	end[0]=20.5000620480408/1000.0; end[1]=19.1339750384809/1000.0;  start[0] = 62.000125628132/1000.0; start[1] = 18.2679500769617/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	
	end[0]=41.0000934550738/1000.0; end[1]=54.6409984607654/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	
	end[0] = 62.000125628132/1000.0; end[1] = 18.2679500769617/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	
	
	start[0] = 500/1000.0;
	end[0] = 0;
	
	//planner.queueMove(start,end,1000);
	
	/*for(int i=0;i<16;i++) {
				p->speed=100;
		p->endPos[0]=10*(i+1);
		p->endPos[1]=0;
		p->endPos[2]=0;
		p->endPos[3]=0;
		planner.queueMove(p->startPos,p->endPos,p->speed);
		prev=p;
		
		
	}*/
	
	delete prev;
	
	//std::this_thread::sleep_for( std::chrono::milliseconds(2000) );
	planner.waitUntilFinished();
	
	planner.stopThread(true);
	
    return 0;
}

