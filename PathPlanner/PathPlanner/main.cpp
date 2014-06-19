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
	
	
	
	
	float start[5],end[5];
	
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
	
	
	float maxFeedrate[3];
	
	maxFeedrate[0]=200; //m/s
	maxFeedrate[1]=200;
	maxFeedrate[2]=5;
	
	unsigned long axisStepsPerMM[3];
	
	axisStepsPerMM[0]=50*1000;
	axisStepsPerMM[1]=50*1000;
	axisStepsPerMM[2]=2133*1000;
	
	float maxAccelerationMMPerSquareSecond[3];
	
	maxAccelerationMMPerSquareSecond[0]=1;
	maxAccelerationMMPerSquareSecond[1]=1;
	maxAccelerationMMPerSquareSecond[2]=0.1;
	
	float maxTravelAccelerationMMPerSquareSecond[3];
	
	maxTravelAccelerationMMPerSquareSecond[0]=2;
	maxTravelAccelerationMMPerSquareSecond[1]=2;
	maxTravelAccelerationMMPerSquareSecond[2]=0.2;
	
	
	planner.setMaxFeedrates(maxFeedrate);
	planner.setAxisStepsPerMeter(axisStepsPerMM);
	planner.setPrintAcceleration(maxAccelerationMMPerSquareSecond);
	planner.setTravelAcceleration(maxTravelAccelerationMMPerSquareSecond);
	
	
	Extruder & extruder = planner.getExtruder(0);
	
	extruder.setAxisStepsPerMeter(535*1000.0);
	extruder.setTravelAcceleration(2);
	extruder.setPrintAcceleration(1);
	extruder.setMaxFeedrate(0.2);
	extruder.setMaxStartFeedrate(20/1000.0);
	
	planner.setExtruder(0);

	
	
	float speed = 3000/60000.0;
	end[0]=96.619/1000.0; end[1]=103.196/1000.0;  start[0] = end[0]; start[1] = end[1]; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=97.959/1000.0; end[1]=103.375/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=99.543/1000.0; end[1]=103.728/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=100.811/1000.0; end[1]=104.128/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=102.319/1000.0; end[1]=104.748/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=103.518/1000.0; end[1]=105.370/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=104.872/1000.0; end[1]=106.222/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=105.076/1000.0; end[1]=106.371/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=106.157/1000.0; end[1]=107.212/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=107.140/1000.0; end[1]=108.113/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=108.255/1000.0; end[1]=109.328/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.063/1000.0; end[1]=110.379/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.926/1000.0; end[1]=111.718/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.554/1000.0; end[1]=112.913/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.697/1000.0; end[1]=113.215/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.192/1000.0; end[1]=114.416/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.600/1000.0; end[1]=115.685/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.692/1000.0; end[1]=116.012/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.972/1000.0; end[1]=117.274/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.032/1000.0; end[1]=117.646/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.193/1000.0; end[1]=118.951/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.250/1000.0; end[1]=120.205/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.251/1000.0; end[1]=138.036/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.270/1000.0; end[1]=141.197/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.327/1000.0; end[1]=144.327/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.421/1000.0; end[1]=148.014/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.708/1000.0; end[1]=155.532/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.954/1000.0; end[1]=160.492/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.974/1000.0; end[1]=161.494/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.935/1000.0; end[1]=162.515/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.840/1000.0; end[1]=163.511/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.691/1000.0; end[1]=164.521/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.483/1000.0; end[1]=165.523/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.220/1000.0; end[1]=166.494/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.890/1000.0; end[1]=167.479/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.510/1000.0; end[1]=168.425/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.075/1000.0; end[1]=169.364/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.584/1000.0; end[1]=170.274/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.039/1000.0; end[1]=171.156/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.447/1000.0; end[1]=171.997/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=108.792/1000.0; end[1]=172.820/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=108.090/1000.0; end[1]=173.600/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=107.346/1000.0; end[1]=174.334/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=106.569/1000.0; end[1]=175.020/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=105.745/1000.0; end[1]=175.666/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=104.901/1000.0; end[1]=176.253/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=103.994/1000.0; end[1]=176.807/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=103.060/1000.0; end[1]=177.304/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=102.101/1000.0; end[1]=177.743/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=101.119/1000.0; end[1]=178.126/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=100.117/1000.0; end[1]=178.451/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=99.122/1000.0; end[1]=178.711/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=98.082/1000.0; end[1]=178.921/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=97.034/1000.0; end[1]=179.069/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=95.982/1000.0; end[1]=179.156/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=95.031/1000.0; end[1]=179.181/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=74.968/1000.0; end[1]=179.181/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=73.932/1000.0; end[1]=179.151/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=72.874/1000.0; end[1]=179.058/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=71.827/1000.0; end[1]=178.904/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=70.794/1000.0; end[1]=178.691/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=69.775/1000.0; end[1]=178.418/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=68.798/1000.0; end[1]=178.095/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=67.807/1000.0; end[1]=177.703/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=66.847/1000.0; end[1]=177.256/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=65.920/1000.0; end[1]=176.756/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=65.027/1000.0; end[1]=176.204/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=64.024/1000.0; end[1]=175.486/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=63.367/1000.0; end[1]=174.964/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=62.584/1000.0; end[1]=174.267/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=61.842/1000.0; end[1]=173.525/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=61.148/1000.0; end[1]=172.745/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.504/1000.0; end[1]=171.928/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.912/1000.0; end[1]=171.077/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.384/1000.0; end[1]=170.214/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.891/1000.0; end[1]=169.291/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.459/1000.0; end[1]=168.346/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.085/1000.0; end[1]=167.403/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.763/1000.0; end[1]=166.427/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.500/1000.0; end[1]=165.437/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.301/1000.0; end[1]=164.465/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.155/1000.0; end[1]=163.448/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.063/1000.0; end[1]=162.450/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.028/1000.0; end[1]=161.432/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.049/1000.0; end[1]=160.492/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.295/1000.0; end[1]=155.534/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.452/1000.0; end[1]=151.611/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.582/1000.0; end[1]=148.014/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.676/1000.0; end[1]=144.327/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.732/1000.0; end[1]=141.197/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.751/1000.0; end[1]=138.036/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.751/1000.0; end[1]=120.321/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.800/1000.0; end[1]=119.092/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.949/1000.0; end[1]=117.809/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.028/1000.0; end[1]=117.300/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.351/1000.0; end[1]=115.866/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.779/1000.0; end[1]=114.503/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.386/1000.0; end[1]=113.043/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.032/1000.0; end[1]=111.796/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.750/1000.0; end[1]=110.655/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=61.748/1000.0; end[1]=109.328/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=62.829/1000.0; end[1]=108.148/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=63.846/1000.0; end[1]=107.212/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=65.150/1000.0; end[1]=106.208/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=66.336/1000.0; end[1]=105.454/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=67.738/1000.0; end[1]=104.724/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=69.249/1000.0; end[1]=104.109/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=70.564/1000.0; end[1]=103.699/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=71.831/1000.0; end[1]=103.416/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=72.154/1000.0; end[1]=103.358/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=73.520/1000.0; end[1]=103.182/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=74.984/1000.0; end[1]=103.120/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=94.958/1000.0; end[1]=103.120/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=95.026/1000.0; end[1]=103.620/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=96.565/1000.0; end[1]=103.694/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=97.876/1000.0; end[1]=103.868/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=99.406/1000.0; end[1]=104.210/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=100.648/1000.0; end[1]=104.601/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=102.105/1000.0; end[1]=105.200/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=103.277/1000.0; end[1]=105.808/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=104.590/1000.0; end[1]=106.635/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=104.775/1000.0; end[1]=106.771/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=105.829/1000.0; end[1]=107.590/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=106.792/1000.0; end[1]=108.472/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=107.868/1000.0; end[1]=109.645/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=108.659/1000.0; end[1]=110.674/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.495/1000.0; end[1]=111.972/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.106/1000.0; end[1]=113.135/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.724/1000.0; end[1]=114.593/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.121/1000.0; end[1]=115.827/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.207/1000.0; end[1]=116.134/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.480/1000.0; end[1]=117.368/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.537/1000.0; end[1]=117.719/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.695/1000.0; end[1]=118.989/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.750/1000.0; end[1]=120.218/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.751/1000.0; end[1]=138.038/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.770/1000.0; end[1]=141.203/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.827/1000.0; end[1]=144.339/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.921/1000.0; end[1]=148.030/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.208/1000.0; end[1]=155.554/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.454/1000.0; end[1]=160.511/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.474/1000.0; end[1]=161.489/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.436/1000.0; end[1]=162.481/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.343/1000.0; end[1]=163.452/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=112.199/1000.0; end[1]=164.433/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.996/1000.0; end[1]=165.406/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.741/1000.0; end[1]=166.350/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.420/1000.0; end[1]=167.307/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=111.051/1000.0; end[1]=168.228/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.628/1000.0; end[1]=169.139/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=110.151/1000.0; end[1]=170.024/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.622/1000.0; end[1]=170.880/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=109.047/1000.0; end[1]=171.697/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=108.410/1000.0; end[1]=172.497/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=107.729/1000.0; end[1]=173.254/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=107.006/1000.0; end[1]=173.968/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=106.249/1000.0; end[1]=174.636/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=105.448/1000.0; end[1]=175.264/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=104.628/1000.0; end[1]=175.834/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=103.746/1000.0; end[1]=176.372/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=102.838/1000.0; end[1]=176.855/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=101.906/1000.0; end[1]=177.283/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=100.951/1000.0; end[1]=177.655/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=99.976/1000.0; end[1]=177.971/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=99.010/1000.0; end[1]=178.224/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=97.998/1000.0; end[1]=178.428/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=96.978/1000.0; end[1]=178.572/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=95.954/1000.0; end[1]=178.656/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=95.025/1000.0; end[1]=178.681/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=74.976/1000.0; end[1]=178.681/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=73.961/1000.0; end[1]=178.652/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=72.932/1000.0; end[1]=178.561/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=71.914/1000.0; end[1]=178.412/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=70.909/1000.0; end[1]=178.204/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=69.918/1000.0; end[1]=177.939/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=68.969/1000.0; end[1]=177.625/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=68.005/1000.0; end[1]=177.244/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=67.072/1000.0; end[1]=176.809/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=66.171/1000.0; end[1]=176.323/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=65.302/1000.0; end[1]=175.786/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=64.468/1000.0; end[1]=175.200/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=63.690/1000.0; end[1]=174.582/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=62.927/1000.0; end[1]=173.903/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=62.205/1000.0; end[1]=173.182/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=61.703/1000.0; end[1]=172.618/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.906/1000.0; end[1]=171.631/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.330/1000.0; end[1]=170.803/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.818/1000.0; end[1]=169.966/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.340/1000.0; end[1]=169.069/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.919/1000.0; end[1]=168.152/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.555/1000.0; end[1]=167.232/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.242/1000.0; end[1]=166.285/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.987/1000.0; end[1]=165.323/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.794/1000.0; end[1]=164.379/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.652/1000.0; end[1]=163.391/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.563/1000.0; end[1]=162.418/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.528/1000.0; end[1]=161.429/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.548/1000.0; end[1]=160.511/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.794/1000.0; end[1]=155.555/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=57.951/1000.0; end[1]=151.632/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.082/1000.0; end[1]=148.030/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.176/1000.0; end[1]=144.339/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.232/1000.0; end[1]=141.203/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.251/1000.0; end[1]=138.038/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.251/1000.0; end[1]=120.332/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.299/1000.0; end[1]=119.121/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.517/1000.0; end[1]=117.403/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=58.832/1000.0; end[1]=116.004/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.250/1000.0; end[1]=114.672/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=59.835/1000.0; end[1]=113.263/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=60.468/1000.0; end[1]=112.042/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=61.168/1000.0; end[1]=110.930/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=62.135/1000.0; end[1]=109.645/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=63.177/1000.0; end[1]=108.507/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=64.174/1000.0; end[1]=107.590/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=65.432/1000.0; end[1]=106.622/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=66.587/1000.0; end[1]=105.887/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=67.944/1000.0; end[1]=105.180/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	end[0]=69.408/1000.0; end[1]=104.583/1000.0; planner.queueMove(start,end,speed,false); start[0] = end[0]; start[1] = end[1];
	

	
	
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

