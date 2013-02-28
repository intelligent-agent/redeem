.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 	19
#define GPIO_DATAOUT 		0x13c				// This is the register for setting data
#define DDR_MAGIC			0xbabe7175			// Magic number used to reset the DDR counter 
#define GPIO1 				0x4804C000			// The adress of the GPIO1 bank
#define GPIO3 				0x481AE000 			// The adress of the GPIO3 bank 
#define GPIO1_MASK			(1<<1)|(1<<2)|(1<<6)|(1<<7)|(1<<12)|(1<<13)|(1<<14)|(1<<30)|(1<<31) // Toggelable
#define GPIO3_MASK			(1<<21)		// Only these two pins are togglable

START:
    LBCO r0, C4, 4, 4							// Load Bytes Constant Offset (?)
    CLR  r0, r0, 4								// Clear bit 4 in reg 0
    SBCO r0, C4, 4, 4							// Store Bytes Constant Offset

	MOV  r10, GPIO1_MASK						// Make the mask
    MOV  r11, GPIO1 | GPIO_DATAOUT				// Load address
    MOV  r12, 0xFFFFFFFF ^ (GPIO1_MASK)			// Invert the mask
	MOV  r16, GPIO3_MASK						// Make the mask
    MOV  r17, GPIO3 | GPIO_DATAOUT				// Load address
    MOV  r18, 0xFFFFFFFF ^ (GPIO3_MASK)			// Invert mask
	
	MOV  r0, 4									// Load the address of the events_counter 
	LBBO r6, r0, 0, 4							// Put it in R6
	MOV  r5, 0									// Make r5 the nr of events counter
	SBBO r5, r6, 0, 4							// store the number of interrupts that have occured in the second reg of DRAM
	
RESET_R4:
	MOV  r0, 0
	LBBO r4, r0, 0, 4							// Load the ddr_addr from the first adress in the PRU0 DRAM
	QBA WAIT									// Check if the end of DDR is reached

BLINK:
	ADD  r4, r4, 4								// Increment r4

    LBBO r2, r4, 0, 4							// Load pin data into r2
	AND  r2, r2, r10							// Mask the pins to GPIO1
	LBBO r3, r11, 0, 4							// Load the data currently in addr r3
	AND	 r3, r3, r12							// Mask the data so only the necessary pins can change
	OR   r3, r3, r2 							// Add the GPIO1-mask to hinder toggling PRU1's pins
    SBBO r3, r11, 0, 4							// Ok, set the pins

    LBBO r2, r4, 0, 4							// Load pin data into r2
	AND  r2, r2, r16							// Mask the pins to GPIO3
	LBBO r3, r17, 0, 4							// Load the data currently in addr r3
	AND	 r3, r3, r18							// Mask the data so only the necessary pins can change
	OR   r3, r3, r2 							// Add the GPIO1-mask to hinder toggling PRU1's pins
    SBBO r3, r17, 0, 4							// Ok, set the pins

	ADD  r4, r4, 4
    LBBO r0, r4, 0, 4							// Load delay data into r0
DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0

    SUB r1, r1, 1
    QBNE BLINK, r1, 0							// Still more pins to go, jump back
	ADD  r4, r4, 4			

	ADD r5, r5, 1								// r5++
	SBBO r5, r6, 0, 4							// store the number of interrupts that have occured in the second reg of DRAM
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   		// Send notification to Host that the instructions are done

	MOV  r3, DDR_MAGIC							// Load the fancy word into r3
	LBBO r2, r4, 0, 4							// Load the next data into r2
	QBEQ RESET_R4, r2, r3						// Check if the end of DDR is reached


WAIT:
    LBBO r1, r4, 0, 4     						// Load values from external DDR Memory into R1
    QBNE BLINK, r1, 0
	QBA WAIT									// Loop back to wait for new data

