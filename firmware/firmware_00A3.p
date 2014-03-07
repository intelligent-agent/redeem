.origin 0
.entrypoint INIT

#define PRU0_ARM_INTERRUPT  19
#define GPIO_DATAOUT        0x13c               // This is the register for setting data 
#define GPIO_DATAIN         0x138               // This is the register for reading data 
#define DDR_MAGIC           0xbabe7175          // Magic number used to reset the DDR counter 
#define GPIO0               0x44E07000          // The adress of the GPIO0 bank
#define GPIO1               0x4804C000          // The adress of the GPIO1 bank
#define GPIO2               0x481AC000          // The adress of the GPIO1 bank
#define GPIO3               0x481AE000          // The adress of the GPIO1 bank

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

#define STEPPER_X_END_MIN   2   //On GPIO 2
#define STEPPER_Y_END_MIN   14  //On GPIO 0
#define STEPPER_Z_END_MIN   30  //On GPIO 0
//#define ENDSTOP_INVERSED    1

#define DIRECTION_MASK    0b00011001  //Specify 1 if a direction pin of 0 goes positive, specify 0 otherwise for all the 5 axis

#define GPIO1_MASK          ((1<<STEPPER_Y_STEP)|(1<<STEPPER_H_STEP)|(1<<STEPPER_H_DIR)|(1<<STEPPER_E_DIR)|(1<<STEPPER_E_STEP)|(1<<STEPPER_X_DIR)) // Only these are togglable
#define GPIO0_MASK          ((1<<STEPPER_Y_DIR)|(1<<STEPPER_Z_STEP)|(1<<STEPPER_Z_DIR)|(1<<STEPPER_X_STEP))                 // Only these are togglable


//We define a structure for commands
.struct SteppersCommand
    .u8     step                //Steppers are defined as 0b000HEZYX
    .u8     direction           //Steppers are defined as 0b000HEZYX
    .u16    options             //Options for the move
    .u32    delay               //number of delay cycle loop to do
.ends



INIT:
    LBCO r0, C4, 4, 4                           // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                              // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4                           // Load back the modified SYSCFG register

    //MOV  r10, GPIO1_MASK                      // Make the mask
    MOV  r17, GPIO1 | GPIO_DATAOUT              // Load address
    MOV  r16, 0xFFFFFFFF ^ (GPIO1_MASK)           // Invert the mask
    //MOV  r16, GPIO0_MASK                      // Make the mask
    MOV  r11, GPIO0 | GPIO_DATAOUT              // Load address
    MOV  r15, 0xFFFFFFFF ^ (GPIO0_MASK)           // Invert mask
    //MOV r18, 0xFFFFFFFF

    MOV  r0, 4                                  // Load the address of the events_counter, written by the host system
    LBBO r6, r0, 0, 4                           // Put it in R6
    MOV  r5, 0                                  // Make r5 the nr of events counter, 0 initially
    SBBO r5, r6, 0, 4                           // store the number of interrupts that have occured in the second reg of DRAM
    
     //Load GPIO0,1,2,3 read register content to the DDR
    MOV  r0, 0                                  //Address in DDR, starts at 0
    LBBO r2, r0, 0, 4
    ADD  r2, r2, 4
    
    MOV  r12, GPIO0 | GPIO_DATAIN                // Load Address
    LBBO r1, r12, 0, 4                           //Read GPIO0 INPUT content
    SBBO r1, r2, 0, 4                           //Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

    MOV  r0, GPIO1 | GPIO_DATAIN                // Load Address
    LBBO r1, r0, 0, 4                           //Read GPIO1 INPUT content
    SBBO r1, r2, 0, 4                           //Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

    MOV  r13, GPIO2 | GPIO_DATAIN                // Load Address
    LBBO r1, r13, 0, 4                           //Read GPIO2 INPUT content
    SBBO r1, r2, 0, 4                           //Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4

    MOV  r0, GPIO3 | GPIO_DATAIN                // Load Address
    LBBO r1, r0, 0, 4                           //Read GPIO3 INPUT content
    SBBO r1, r2, 0, 4                           //Put GPIO INPUT content into local RAM

    LBBO r9, r11, 0,   4                         // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                         // Load pin data into r8 which is 4 bytes

    AND r9, r9, r15
    AND r10, r10, r16

    //Store back the value
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //MOV R31.b0, PRU0_ARM_INTERRUPT+16           // Send notification to Host that the instructions are done

RESET_R4:
    MOV  r0, 0
    LBBO r4, r0, 0, 4                           // Load the ddr_addr from the first adress in the PRU0 DRAM
    QBA WAIT                                    // Check if the end of DDR is reached

PINS:
    ADD  r4, r4, 4                              // The next DDR reading address is incremented by 4.    

NEXT_COMMAND:
    //Load a command
    .enter CommandScope

    LBBO r2, r4, 0, 8                           // Load pin command into r2 and r3, which is 8 bytes
    .assign SteppersCommand, r2,r3, pinCommand   // Assign the struct spanning onto r2 and r3

    //Translate the commands into pins
    //First load the direction pins

    //Store the pins of GPIO0 into r7 and GPUI1 into r8

    //FILL  7, 8                                // Store 0xFFFFFFFF into r7,r8
    MOV r7, 0
    MOV r8, 0
    
    //Stepper X
    AND  r9,  pinCommand.direction, 0x01
    LSL  r9, r9, STEPPER_X_DIR
    OR  r8, r8, r9

    //Stepper Y
    LSR  r9, pinCommand.direction, 0x01
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Y_DIR
    OR  r7, r7, r9

    //Stepper Z
    LSR  r9, pinCommand.direction, 0x02
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Z_DIR
    OR  r7, r7, r9

    //Stepper E
    LSR  r9, pinCommand.direction, 0x03
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_E_DIR
    OR  r8, r8, r9

    //Stepper H
    LSR  r9, pinCommand.direction, 0x04
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_H_DIR
    OR  r8, r8, r9

    //Setup direction pin
    LBBO r9, r11, 0,   4                         // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                         // Load pin data into r8 which is 4 bytes

    AND  r9, r9, r15 //Set GPIO 0
    AND  r10, r10, r16 //Set GPIO 1

    OR  r9, r9, r7 //Set GPIO 0
    OR  r10, r10, r8 //Set GPIO 1

    MOV r18,r7
    MOV r19,r8

    //Store back the value
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //32 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND

    //Build GPIO for steps



    //Read the endstop state and mask step with it
    LBBO r9, r12, 0,   4  //GPIO0
    LBBO r10, r13, 0,   4  //GPIO2

    //X
    LSR r0,r10,STEPPER_X_END_MIN     
    AND r7.b0,r0,0x01
    
    //Y
    LSR r0,r9,STEPPER_Y_END_MIN     
    AND r0,r0,0x01
    LSL r0,r0,0x01
    OR  r7.b0,r7.b0,r0

    //Z
    LSR r0,r9,STEPPER_Z_END_MIN     
    AND r0,r0,0x01
    LSL r0,r0,0x02
    OR  r7.b0,r7.b0,r0

    //Inverse it as endstops are inversed

#ifdef ENDSTOP_INVERSED
    XOR r7.b0,r7.b0,0xFF
#endif
    
    XOR r7.b1,pinCommand.direction, DIRECTION_MASK

    OR r7.b0,r7.b1,r7.b0 

    //Only for axis X,Y,Z, the other are untouched
    OR r7.b0,r7.b0,0xF8

    //Check if this is a cancellable move
    QBNE notcancel, pinCommand.options, 0x01

    //Check if we need to cancel the move, we have to if the step is 1 and the endstop is 0
    AND r7.b1,pinCommand.step,r7.b0


    QBEQ notcancel, r7.b1,pinCommand.step

    //Remove all the command from the buffer
start_loop_remove:
    ADD  r4, r4, SIZE(SteppersCommand)
    SUB r1, r1, 1                               //r1 contains the number of PIN instructions in the DDR, we remove one.
    QBNE start_loop_remove, r1, 0                            // Still more pins to go, jump back

    QBA CANCEL_COMMAND_AFTER

notcancel:
    AND pinCommand.step,pinCommand.step,r7.b0




    //FILL  7, 8                                // Store 0xFFFFFFFF into r7,r8
    MOV r7, 0
    MOV r8, 0

    //Stepper X
    AND  r9,  pinCommand.step, 0x01
    LSL  r9, r9, STEPPER_X_STEP
    OR  r7, r7, r9

    //Stepper Y
    LSR  r9, pinCommand.step, 0x01
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Y_STEP
    OR  r8, r8, r9

    //Stepper Z
    LSR  r9, pinCommand.step, 0x02
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_Z_STEP
    OR  r7, r7, r9

    //Stepper E
    LSR  r9, pinCommand.step, 0x03
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_E_STEP
    OR  r8, r8, r9

    //Stepper H
    LSR  r9, pinCommand.step, 0x04
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_H_STEP
    OR  r8, r8, r9


    //Add directions

    OR r7,r7,r18
    OR r8,r8,r19

    //73 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND
    //41 instructions since the direction command

    //We have to wait 650 ns => 130 instructions - 41 instructions
    MOV r0,45
DELAY3:
    SUB r0, r0, 1
    QBNE DELAY3, r0, 0

    //164 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND



    //Setup direction pin
    LBBO r9, r11, 0,   4                         // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                         // Load pin data into r8 which is 4 bytes

    AND  r9, r9, r15 //Set GPIO 0
    AND  r10, r10, r16 //Set GPIO 1

    OR  r9, r9, r7 //Set GPIO 0
    OR  r10, r10, r8 //Set GPIO 1

    //Store back the value
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //176 INSTRUCTIONS UNTIL HERE

    AND r9, r9, r15
    AND r10, r10, r16

    //Increment reading address
    ADD  r4, r4, SIZE(SteppersCommand)

    //We have to wait 380 instructions - 3 = 377   

    MOV r0,189
DELAY2:
    SUB r0, r0, 1
    QBNE DELAY2, r0, 0

    //put the step pin to low
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    //We need to have a min delay of 1.9us until the next steps =>  380 instructions

    MOV  r0, pinCommand.delay

    //561 INSTRUCTIONS UNTIL HERE

    //We substract the time to setup a step to the delay to be more precise
    MOV r9,576
    MAX r0,r0,r9
    SUB r0,r0,r9


    MAX  r0,r0,190

    //Now execute the delay, with the proper substraction
    .leave CommandScope

DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0


    SUB r1, r1, 1                               //r1 contains the number of PIN instructions in the DDR, we remove one.
    QBNE NEXT_COMMAND, r1, 0                            // Still more pins to go, jump back
    //ADD  r4, r4, 4                                // The next DDR reading address is incremented by 4.            

CANCEL_COMMAND_AFTER:

    ADD r5, r5, 1                               // r5++, r5 is the event_counter.
    SBBO r5, r6, 0, 4                           // store the number of interrupts that have occured in the second reg of DRAM
    MOV R31.b0, PRU0_ARM_INTERRUPT+16           // Send notification to Host that the instructions are done

    MOV  r3, DDR_MAGIC                          // Load the fancy word into r3
    LBBO r2, r4, 0, 4                           // Load the next data into r2
    QBEQ RESET_R4, r2, r3                       // Check if the end of DDR is reached


WAIT:
    LBBO r1, r4, 0, 4                           // Load values from external DDR Memory into R1
    QBNE PINS, r1, 0                            // Start to process the pins stored in DDR if we have a value != of 0 stored in the current location of the DDR
    QBA WAIT                                    // Loop back to wait for new data

