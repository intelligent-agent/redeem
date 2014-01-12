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
#define GPIO1_MASK			(1<<12)|(1<<13)|(1<<14)|(1<<15)|(1<<28)|(1<<29) // Only these are togglable
#define GPIO0_MASK			(1<<22)|(1<<23)|(1<<26)|(1<<27)					// Only these are togglable

INIT:
    LBCO r0, C4, 4, 4							// Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4								// Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4							// Load back the modified SYSCFG register

	MOV  r10, GPIO1_MASK						// Make the mask
    MOV  r11, GPIO1 | GPIO_DATAOUT				// Load address
    MOV  r12, 0xFFFFFFFF ^ (GPIO1_MASK)			// Invert the mask
	MOV  r16, GPIO0_MASK						// Make the mask
    MOV  r17, GPIO0 | GPIO_DATAOUT				// Load address
    MOV  r18, 0xFFFFFFFF ^ (GPIO0_MASK)			// Invert mask
	
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

    LBBO r2, r4, 0, 4							// Load pin data into r2, which is 4 bytes
	AND  r2, r2, r10							// Mask the pins to GPIO1
	LBBO r3, r11, 0, 4							// Load the current GPIO1 data into r3
	AND	 r3, r3, r12							// Mask the data so only the necessary pins can change
	OR   r3, r3, r2 							// Add the GPIO1-mask to hinder toggling PRU0's pins
    SBBO r3, r11, 0, 4							// Ok, set the pins by putting back GPIO1 register data

    LBBO r2, r4, 0, 4							// Load pin data into r2
	AND  r2, r2, r16							// Mask the pins to GPIO0
	LBBO r3, r17, 0, 4							// Load the data currently in addr r3
	AND	 r3, r3, r18							// Mask the data so only the necessary pins can change
	OR   r3, r3, r2 							// Add the GPIO0-mask to hinder toggling PRU1's pins
    SBBO r3, r17, 0, 4							// Ok, set the pins

	ADD  r4, r4, 4
    LBBO r0, r4, 0, 4							// Load delay data into r0
DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0

    MOV  r0, 8									// Check for the emergency stop flag
    LBBO r2, r0, 0, 4
    QBNE EMERGENCY_STOP, r2, 0

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


EMERGENCY_STOP:
	MOV  r5, 0									// Make r5 the nr of events counter, 0 initially
	SBBO r5, r6, 0, 4
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   		// Send notification to Host that the instructions are done
	QBA RESET_R4
