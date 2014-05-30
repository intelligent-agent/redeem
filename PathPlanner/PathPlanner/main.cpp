//
//  main.cpp
//  PathPlanner
//
//  Created by Mathieu on 29.05.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#include <iostream>
#include "PathPlanner.h"

int main(int argc, const char * argv[])
{
	logger << "Start test program" << std::endl;
	

	PathPlanner planner;
	Path *prev=NULL;
	
	planner.initPRU("/root/redeem/firmware/firmware_runtime.bin","/root/redeem/firmware/firmware_endstops.bin");
	
	planner.runThread();
	
	
	float start[5],end[5];
	
	bzero(start,5*4);
	bzero(end,5*4);
	end[2] = 2133*100;
	
	planner.queueMove(start,end,1000);
	
	start[0] = 500;
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

