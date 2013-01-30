.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define PRU1_ARM_INTERRUPT 20

#define GPIO1 			0x4804c000		// The adress of the GPIO1 
#define GPIO3 			0x481ae000 		// The adress of the GPIO3 
#define GPIO_DATAOUT 	0x13c			// This is the register for settign data
#define LEN_ADDR		0x00000000		// Adress of the abort command			
#define PIN_OFFSET		0x00000004  	// Offset for the pins (reserve the first adress for abort)
#define GPIO1_MASK		(1<<12)|(1<<13)|(1<<30)|(1<<31)
#define GPIO3_MASK		(1<<19)|(1<<21) 

START:	
    LBCO r0, C4, 4, 4					// clear that bit
    CLR  r0, r0, 4						// No, really, clear it!
    SBCO r0, C4, 4, 4					// Actually i have no idea what this does

	MOV  r0, 0							// The first register contains the loop count
    LBBO r1, r0, 0, 4					// Load the number of steps to perform into r1
	QBEQ EXIT, r1, 0					// Exit if the counter r1 is 0
	MOV  r4, PIN_OFFSET					// r4 is the pin and delay counter
SET_PINS:						
    LBBO r2, r4, 0, 4					// Load pin data into r2
	MOV  r3, GPIO1_MASK
	AND  r2, r2, r3
    MOV  r3, GPIO1 | GPIO_DATAOUT 		// Load the address of GPIO | DATAOUT in r3
    SBBO r2, r3, 0, 4					// Set the pins

    LBBO r2, r4, 0, 4					// Load pin data into r2
	MOV  r3, GPIO3_MASK
	AND  r2, r2, r3
	MOV  r3, GPIO3 | GPIO_DATAOUT		// Load the adress of GPIO3
    SBBO r2, r3, 0, 4					// Set the pins

	ADD  r4, r4, 4						// r4 += 4
	LBBO r0, r4, 0, 4					// Load Delay into r0
DELAY:									
    SUB  r0, r0, 1						// Delay the required ticks
    QBNE DELAY, r0, 0					

	ADD  r4, r4, 4						// r4 += 4
    SUB  r1, r1, 1						// Decrement r1
    QBNE SET_PINS, r1, 0				// Branch back to SET_PINS if r0 != 0, abort!

EXIT:
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
