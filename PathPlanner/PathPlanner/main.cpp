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
	
	planner.runThread();
	
	
	float start[5],end[5];
	
	bzero(start,5*4);
	bzero(end,5*4);
	end[2] = 10/1000.0;
	
	planner.queueMove(start,end,1000/1000.0,true);
	
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

