//
//  StepperCommand.h
//  PathPlanner
//
//  Created by Mathieu on 01.06.14.
//  Copyright (c) 2014 Xwaves. All rights reserved.
//

#ifndef PathPlanner_StepperCommand_h
#define PathPlanner_StepperCommand_h

#include <stdint.h>

typedef struct SteppersCommand {
	uint8_t     step  ;              //Steppers are defined as 0b000HEZYX - A 1 for a stepper means we will do a step for this stepper
	uint8_t     direction ;          //Steppers are defined as 0b000HEZYX - Direction for each stepper
	uint16_t    options   ;          //Options for the move - If the first bit is set to 1, then the stepper has the cancelable
	//option meaning that as soon as an endstop is hit, all the moves in the DDR are removed and canceled without making the steppers to move.
	uint32_t    delay    ;           //number of cycle to wait (this is the # of PRU click cycles)
} SteppersCommand;

static_assert(sizeof(SteppersCommand)==8,"Invalid stepper command size");

#endif
