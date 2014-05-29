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

	PathPlanner planner;
	Path *prev=NULL;
	
	planner.initPRU("ss", "ss");
	
	planner.runThread();
	
	for(int i=0;i<1;i++) {
		Path * p =new Path();
		bzero(p,sizeof(*p));
		
		if(prev) {
			memcpy(p->startPos, prev->endPos, sizeof(p->startPos));
			delete prev;
		}
		p->speed=70;
		p->endPos[0]=100*(i+1);
		p->endPos[1]=0;
		p->endPos[2]=0;
		p->endPos[3]=0;
		planner.queueMove(p->startPos,p->endPos,p->speed);
		prev=p;
		
		
	}
	
	delete prev;
	
	std::this_thread::sleep_for( std::chrono::milliseconds(2000) );
	
	planner.stopThread(true);
	
    return 0;
}

