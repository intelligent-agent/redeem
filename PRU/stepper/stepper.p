.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define AM33XX

#define GPIO1 			0x4804c000
#define GPIO_DATAOUT 	0x13c
#define ABORT_ADDR		0x00000000		// Adress of the abort command			
#define DLY_OFFSET		44				// Offset for delays (half of the available memory)
#define PIN_OFFSET		4				// Offset for the pins (reserve the first adress for abort)

START:	
    LBCO r0, C4, 4, 4					// clear that bit
    CLR  r0, r0, 4
    SBCO r0, C4, 4, 4

	MOV  r4, 0							// r4 is the pin/delay counter
SET_PINS:						
    LBBO r2, r4, PIN_OFFSET, 4			// Load pin data into r2
    MOV  r3, GPIO1 | GPIO_DATAOUT 		// Load the address of GPIO | DATAOUT in r3
    SBBO r2, r3, 0, 4					// Set the pins

	LBBO r0, r4, DLY_OFFSET, 4			// Load Delay into r0
	QBEQ EXIT, r0, 0					// If the delay is 0, exit, no more commands.  
DELAY:									
    SUB  r0, r0, 1						// Delay the required ticks
    QBNE DELAY, r0, 0					

	ADD  r4, r4, 4						// r4 += 4
	MOV  r1, ABORT_ADDR					// Load the abort address
    LBBO r0, r1, 0, 4					// Load the content of the first adress 
    QBNE SET_PINS, r0, 0				// Branch back to SET_PINS if r0 != 0, abort!

EXIT:
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
