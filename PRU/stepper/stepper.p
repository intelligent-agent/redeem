.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define AM33XX

#define GPIO1 0x4804c000
#define GPIO_CLEARDATAOUT 0x190
#define GPIO_SETDATAOUT 0x194
#define MEM_START 0x00000000
#define CMD_OFFSET	10*4				// Offset for the commands

START:
	// clear that bit
    LBCO r0, C4, 4, 4
    CLR r0, r0, 4
    SBCO r0, C4, 4, 4

	MOV r4, MEM_START					// r4 = 0x00
    MOV r1, 10							// r1 = 10

STEP:									// do{ 
    LBBO r2, r4, CMD_OFFSET, 4			// 	r2 = *(r4+cmd_offset)
    MOV r3, GPIO1 | GPIO_SETDATAOUT 	// 	r3 = set data GPIO1 register
    SBBO r2, r3, 0, 4					// 	Copy 4 bytes from r2 to *r3

	MOV r0, 0x00f00000					// r0 = 0x00f00000
DELAY_ON:								// do{
    SUB r0, r0, 1						// 	r0--
    QBNE DELAY_ON, r0, 0				// } while(r0);

// Off
    LBBO r2, r4, CMD_OFFSET, 4			// r2 = *(r4+cmd_offset)
    MOV r3, GPIO1 | GPIO_CLEARDATAOUT 	// r3 = clear data in GPIO1 register
    SBBO r2, r3, 0, 4					// copy 4 bytes from r2 to *r3

    LBBO r0, r4, 0, 4					// r0 = *r4
	ADD r4, r4, 4						// r4 += 4

DELAY_OFF:								// do{
    SUB r0, r0, 1						// 	r0--
    QBNE DELAY_OFF, r0, 0				// }while(r0);

    SUB r1, r1, 1						// r1--
    QBNE STEP, r1, 0					// }while(r1);

    MOV R31.b0, PRU0_ARM_INTERRUPT+16     // Send notification to Host for program completion
HALT
