.origin 0
.entrypoint INIT

#define PRU0_ARM_INTERRUPT 	19
#define GPIO_DATAOUT 		0x13c				// This is the register for setting data 
#define GPIO_DATAIN 		0x138				// This is the register for reading data 
#define DDR_MAGIC			0xbabe7175			// Magic number used to reset the DDR counter 
#define GPIO0 				0x44E07000 			// The adress of the GPIO0 bank
#define GPIO1 				0x4804C000			// The adress of the GPIO1 bank
#define GPIO2 				0x481AC000			// The adress of the GPIO1 bank
#define GPIO3 				0x481AE000			// The adress of the GPIO1 bank

#define STEPPER_X_STEP      27  //On GPIO 0
#define STEPPER_Y_STEP      12  //On GPIO 1
#define STEPPER_Z_STEP      23  //On GPIO 0
#define STEPPER_E_STEP      28  //On GPIO 1
#define STEPPER_H_STEP      13  //On GPIO 1

#define STEPPER_X_DIR       29  //On GPIO 1
#define STEPPER_Y_DIR       22  //On GPIO 0
#define STEPPER_Z_DIR       26  //On GPIO 0
#define STEPPER_E_DIR       15  //On GPIO 1
#define STEPPER_H_DIR       14  //On GPIO 1

#define GPIO1_MASK          ((1<<STEPPER_Y_STEP)|(1<<STEPPER_H_STEP)|(1<<STEPPER_H_DIR)|(1<<STEPPER_E_DIR)|(1<<STEPPER_E_STEP)|(1<<STEPPER_X_DIR)) // Only these are togglable
#define GPIO0_MASK          ((1<<STEPPER_Y_DIR)|(1<<STEPPER_Z_STEP)|(1<<STEPPER_Z_DIR)|(1<<STEPPER_X_STEP))                 // Only these are togglable


//We define a structure for commands
.struct SteppersCommand
    .u8     step                //Steppers are defined as 0b000HEZYX
    .u8     direction           //Steppers are defined as 0b000HEZYX
    .u16    notused             //For future usage
    .u32    delay               //number of delay cycle loop to do
.ends


INIT:
    LBCO r0, C4, 4, 4							// Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4								// Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4							// Load back the modified SYSCFG register

	//MOV  r10, GPIO1_MASK						// Make the mask
    MOV  r11, GPIO1 | GPIO_DATAOUT				// Load address
    //MOV  r12, 0xFFFFFFFF ^ (GPIO1_MASK)			// Invert the mask
	//MOV  r16, GPIO0_MASK						// Make the mask
    MOV  r17, GPIO0 | GPIO_DATAOUT				// Load address
   // MOV  r18, 0xFFFFFFFF ^ (GPIO0_MASK)			// Invert mask
	//MOV r18, 0xFFFFFFFF

	MOV  r0, 4									// Load the address of the events_counter, written by the host system
	LBBO r6, r0, 0, 4							// Put it in R6
	MOV  r5, 0									// Make r5 the nr of events counter, 0 initially
	SBBO r5, r6, 0, 4							// store the number of interrupts that have occured in the second reg of DRAM
	
	 //Load GPIO0,1,2,3 read register content to the DDR
    MOV	 r0, 0									//Address in DDR, starts at 0
    LBBO r2, r0, 0, 4
    ADD  r2, r2, 4
    
    MOV  r0, GPIO0 | GPIO_DATAIN				// Load Address
    LBBO r1, r0, 0, 4							//Read GPIO0 INPUT content
    SBBO r1, r2, 0, 4							//Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

    MOV  r0, GPIO1 | GPIO_DATAIN				// Load Address
    LBBO r1, r0, 0, 4							//Read GPIO1 INPUT content
    SBBO r1, r2, 0, 4							//Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

  	MOV  r0, GPIO2 | GPIO_DATAIN				// Load Address
    LBBO r1, r0, 0, 4							//Read GPIO2 INPUT content
    SBBO r1, r2, 0, 4							//Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

  	MOV  r0, GPIO3 | GPIO_DATAIN				// Load Address
    LBBO r1, r0, 0, 4							//Read GPIO3 INPUT content
    SBBO r1, r2, 0, 4							//Put GPIO INPUT content into local RAM



RESET_R4:
	MOV  r0, 0
	LBBO r4, r0, 0, 4							// Load the ddr_addr from the first adress in the PRU0 DRAM
	QBA WAIT									// Check if the end of DDR is reached

PINS:
	ADD  r4, r4, 4								// Increment r4, the reading location of DDR by 4 bytes

    //Load a command
    .enter CommandScope

    LBBO r2, r4, 0, 4                           // Load pin command into r2 and r3, which is 8 bytes
    .assign SteppersCommand, r2,r3, pinCommand   // Assign the struct spanning onto r2 and r3

    //Translate the commands into pins
    //First load the direction pins

    //Store the pins of GPIO0 into r7 and GPUI1 into r8

    FILL  7, 8                                // Store 0xFFFFFFFF into r7,r8
    
    //Stepper X
    AND  r9,  pinCommand.direction, 0x01
    LSL  r9, r9, STEPPER_X_DIR
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_X_DIR)
    OR   r9, r9, r10
    AND  r8, r8, r9

    //Stepper Y
    LSR  r9, pinCommand.direction, 0x02
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Y_DIR
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_Y_DIR)
    OR   r9, r9, r10
    AND  r7, r7, r9

    //Stepper Z
    LSR  r9, pinCommand.direction, 0x03
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Z_DIR
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_Z_DIR)
    OR   r9, r9, r10
    AND  r7, r7, r9

    //Stepper E
    LSR  r9, pinCommand.direction, 0x04
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_E_DIR
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_E_DIR)
    OR   r9, r9, r10
    AND  r8, r8, r9

    //Stepper H
    LSR  r9, pinCommand.direction, 0x05
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_H_DIR
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_H_DIR)
    OR   r9, r9, r10
    AND  r8, r8, r9

    //Setup direction pin
    LBBO r9, r11, 0,   4                         // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                         // Load pin data into r8 which is 4 bytes

    AND  r9, r9, r7 //Set GPIO 0
    AND  r10, r10, r8 //Set GPIO 1

    //Store back the value
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //At that point the pins are set, from that point to the next set of the pin 650 NS should be spent
#define DIRECTION_WAIT 650 //In nano seconds
#define pru_hz 200000000 //200 MHZ
#define CYCLE_PER_NANOSECOND    (pru_hz/1000000)
#define DIRECTION_NB_CYCLE (DIRECTION_WAIT/CYCLE_PER_NANOSECOND)   //In number of CPU cycles, PRU is 200 MHZ, 

    //Build GPIO for steps

    FILL  7, 8                                // Store 0xFFFFFFFF into r7,r8
    
    //Stepper X
    AND  r9,  pinCommand.step, 0x01
    LSL  r9, r9, STEPPER_X_STEP
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_X_STEP)
    OR   r9, r9, r10
    AND  r7, r7, r9

    //Stepper Y
    LSR  r9, pinCommand.step, 0x02
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Y_STEP
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_Y_STEP)
    OR   r9, r9, r10
    AND  r8, r8, r9

    //Stepper Z
    LSR  r9, pinCommand.step, 0x03
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Z_STEP
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_Z_STEP)
    OR   r9, r9, r10
    AND  r7, r7, r9

    //Stepper E
    LSR  r9, pinCommand.step, 0x04
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_E_STEP
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_E_STEP)
    OR   r9, r9, r10
    AND  r8, r8, r9

    //Stepper H
    LSR  r9, pinCommand.step, 0x05
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_H_STEP
    MOV  r10, 0xFFFFFFFF ^ (1 << STEPPER_H_STEP)
    OR   r9, r9, r10
    AND  r8, r8, r9

    .leave CommandScope

    //Here we have to wait DIRECTION_NB_CYCLE - 25 - 1 instructions which corresponds to the step instructions building
    //This comes down to < 0 instructions so we don't do anything

    //Setup direction pin
    LBBO r9, r11, 0,   4                         // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                         // Load pin data into r8 which is 4 bytes

    AND  r9, r9, r7 //Set GPIO 0
    AND  r10, r10, r8 //Set GPIO 1

    //Store back the value
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //here we have to wait at least 10 instructions before putting the step to 0, we will implicitly do that with the next instructions
    //Set the step pins and dir pins to 0

    MOV r0, (0xFFFFFFFF ^ GPIO0_MASK)
    AND r9, r9, r0
    MOV r0, (0xFFFFFFFF ^ GPIO1_MASK)
    AND r10, r10, r0

    //Increment reading address
    ADD  r4, r4, SIZE(SteppersCommand)
    LBBO r0, r4, 0, 4                           // Load delay data into r0
    ADD  r4, r4, 4


    //We have 81 instructions until here
    //74 instructions were for setuping the step
    //7 instructions were after the step

    // => 81 cycles, substract it from our delay (there will be three mores due to SBBO and NOP) (this will be therefore 86)
    MAX  r0, r0, 87 //+1 so that the sub is 0 after delay
    SUB  r0, r0, 86

    //Needed for delay
    ADD r0, r0, 0

    //put the step pin to low
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //Now execute the delay, with the proper substraction

DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0

    SUB r1, r1, 1 								//r1 contains the number of PIN instructions in the DDR, we remove one.
    QBNE PINS, r1, 0							// Still more pins to go, jump back
	ADD  r4, r4, 4								// The next DDR reading address is incremented by 4.			

	ADD r5, r5, 1								// r5++, r5 is the event_counter.
	SBBO r5, r6, 0, 4							// store the number of interrupts that have occured in the second reg of DRAM
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   		// Send notification to Host that the instructions are done

	MOV  r3, DDR_MAGIC							// Load the fancy word into r3
	LBBO r2, r4, 0, 4							// Load the next data into r2
	QBEQ RESET_R4, r2, r3						// Check if the end of DDR is reached


WAIT:
    LBBO r1, r4, 0, 4     						// Load values from external DDR Memory into R1
    QBNE PINS, r1, 0 							// Start to process the pins stored in DDR if we have a value != of 0 stored in the current location of the DDR
	QBA WAIT									// Loop back to wait for new data

