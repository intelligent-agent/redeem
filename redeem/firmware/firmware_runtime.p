.origin 0
.entrypoint INIT

//* CONFIGURATION SECTION */
//*************************/

#include "config.h"

//* PRU Register and constants */
#define PRU_SPEED           200000000               //PRU clock speed in Hz - Should be 200'000'000 - IF YOU CHANGE IT YOU NEED TO RECOMPUTE ALL THE DELAYS.
#define CYCLE_TO_NS         1000000000/PRU_SPEED    //Number of cycles in 1 ns
#define NS_TO_CYCLE         PRU_SPEED/1000000000    //Number of ns in one cycle

#define PRU0_ARM_INTERRUPT  35
#define PRU1_ARM_INTERRUPT  36
#define GPIO_DATAOUT        0x13c                   // This is the register for setting data 
#define GPIO_CLEARDATAOUT   0x190
#define GPIO_SETDATAOUT     0x194
#define GPIO0               0x44E07000              // The adress of the GPIO0 bank
#define GPIO1               0x4804C000              // The adress of the GPIO1 bank
#define GPIO2               0x481AC000              // The adress of the GPIO2 bank
#define GPIO3               0x481AE000              // The adress of the GPIO3 bank
#define PRU0_CONTROL_REGISTER_BASE      0x00022000                              //The base address for all the PRU1 control registers
#define CTPPR0_REGISTER                 PRU0_CONTROL_REGISTER_BASE + 0x28       //The CTPPR0 register for programming C28 and C29 entries
#define SHARED_RAM_ENDSTOPS_ADDR        0x0120

//* Magic number set by the host for DDR reset */
#define DDR_MAGIC           0xbabe7175          // Magic number used to reset the DDR counter 


#define STEPPER_GPIO_0  r23
#define STEPPER_GPIO_1  r24
#define STEPPER_GPIO_2  r25
#define STEPPER_GPIO_3  r26


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


//We define a structure for commands send to the PRU and stored in DDR
.struct SteppersCommand
    .u8     step                //Steppers are defined as 0b000HEZYX - A 1 for a stepper means we will do a step for this stepper
    .u8     direction           //Steppers are defined as 0b000HEZYX - Direction for each stepper
    .u8     cancellableMask     //If the endstop match the mask, all the move commands are canceled. 
    .u8     options             //Options for the move, bit 0 indicates that a sync interrupt is required. bit 1 indicates that after the sync, suspend.
    .u32    delay               //number of cycle to wait (this is the # of PRU click cycles)
.ends


// Global register used:
//
// r1 : Remaining number of commands to process since we started to read DRAM
// r4 : Current command reading address in DRAM
// r5 : Event counter
// r6 : Address in DRAM where to put the events counter
// r7 : STEPPER_GPIO_0
// r8 : STEPPER_GPIO_1
// r9 : STEPPER_GPIO_2
// r10: STEPPER_GPIO_3

// r11: Adress for setting GPIO0 OUT pins
// r12: Adress for setting GPIO1 OUT pins
// r13: Adress for setting GPIO2 OUT pins
// r14: Adress for setting GPIO3 OUT pins

// r15: Inverted mask for GPIO0 togglable pin
// r16: Inverted mask for GPIO1 togglable pin
// r17: Adress for reading/writing GPIO1 OUT pins
// r20: GPIO1_IN

// r21: Stepper direction mask
// r22: Counts steps remaining - used for bed probing

// r23: Adress for reading/writing GPIO2 OUT pins
// r24: Adress for reading/writing GPIO3 OUT pins


// r25: Inverted mask for GPIO2 togglable pin
// r26: Inverted mask for GPIO3 togglable pin
// r27: Address of PRU control

INIT:
    LBCO r0, C4, 4, 4                                       // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                                          // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4                                       // Load back the modified SYSCFG register
    
    MOV  r0, SHARED_RAM_ENDSTOPS_ADDR                       // Set the C28 address for shared ram, C29 is set to 0
    MOV  r1, CTPPR0_REGISTER
    SBBO r0, r1, 0, 4
    
    MOV  r0, 4                                              // Load the address of the events_counter, written by the host system
    LBBO r6, r0, 0, 4                                       // Put it in R6
    MOV  r5, 0                                              // Make r5 the nr of events counter, 0 initially
    SBBO r5, r6, 0, 4                                       // store the number of interrupts that have occured in the second reg of DRAM

    MOV  r0, 8                                              // Load the address of the pru_control, written by the host system
    LBBO r27, r0, 0, 4                                      // Put it in R27
        
    //Set all the stepper pins to 0 
    MOV STEPPER_GPIO_0, GPIO0_MASK
    MOV STEPPER_GPIO_1, GPIO1_MASK
    MOV STEPPER_GPIO_2, GPIO2_MASK
    MOV STEPPER_GPIO_3, GPIO3_MASK

    MOV r0, GPIO0 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_0, r0, 0, 4
    MOV r0, GPIO1 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_1, r0, 0, 4
    MOV r0, GPIO2 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_2, r0, 0, 4
    MOV r0, GPIO3 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_3, r0, 0, 4

    // Set remaining steps counter to 0
    MOV r22, 0
    
RESET_R4:   
    MOV  r0, 0  
    LBBO r4, r0, 0, 4                                       // Load the ddr_addr from the first adress in the PRU0 DRAM
    QBA WAIT                                                // Check if the end of DDR is reached
    
PINS:   
    ADD  r4, r4, 4                                          // The next DDR reading address is incremented by 4.    
    
NEXT_COMMAND:   
    //Load a command    
    .enter CommandScope 
    
    LBBO r2, r4, 0, 8                                       // Load pin command into r2 and r3, which is 8 bytes
    .assign SteppersCommand, r2,r3, pinCommand              // Assign the struct spanning onto r2 and r3

    //First load the direction pins    
    XOR r21,pinCommand.direction,DIRECTION_MASK             // Invert the stepper direction mask
    AND r21,r21,0xFF                                        // Mask the direction to the last 8 bits

    //Store the pins of the banks in registers
    MOV STEPPER_GPIO_0, 0
    MOV STEPPER_GPIO_1, 0
    MOV STEPPER_GPIO_2, 0
    MOV STEPPER_GPIO_3, 0

    //Stepper X
    AND  r0,  r21, 0x01
    LSL  r0, r0, STEPPER_X_DIR_PIN    
    OR  STEPPER_X_DIR_BANK, STEPPER_X_DIR_BANK, r0          // Put a 1/0 into the pin register for the stepper direction
    
    //Stepper Y     
    LSR  r0, r21, 0x01     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_Y_DIR_PIN      
    OR  STEPPER_Y_DIR_BANK, STEPPER_Y_DIR_BANK, r0
    
    //Stepper Z     
    LSR  r0, r21, 0x02     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_Z_DIR_PIN      
    OR  STEPPER_Z_DIR_BANK, STEPPER_Z_DIR_BANK, r0
    
    //Stepper E     
    LSR  r0, r21, 0x03     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_E_DIR_PIN      
    OR  STEPPER_E_DIR_BANK, STEPPER_E_DIR_BANK, r0
    
    //Stepper H
    LSR  r0, r21, 0x04     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_H_DIR_PIN      
    OR  STEPPER_H_DIR_BANK, STEPPER_H_DIR_BANK, r0

#ifdef STEPPER_A_DIR_BANK
    //Stepper A
    LSR  r0, r21, 0x05     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_A_DIR_PIN      
    OR  STEPPER_A_DIR_BANK, STEPPER_A_DIR_BANK, r0

    //Stepper B
    LSR  r0, r21, 0x06     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_B_DIR_PIN      
    OR  STEPPER_B_DIR_BANK, STEPPER_B_DIR_BANK, r0
#endif
#ifdef STEPPER_C_DIR_BANK
    //Stepper C
    LSR  r0, r21, 0x07     
    AND  r0, r0, 0x01   
    LSL  r0, r0, STEPPER_C_DIR_PIN      
    OR  STEPPER_C_DIR_BANK, STEPPER_C_DIR_BANK, r0
#endif

    // GPIO0 
    MOV r0, GPIO0 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_0, r0, 0, 4           // Set the dirs
    MOV r0, GPIO0 | GPIO_CLEARDATAOUT
    MOV r7, GPIO0_DIR_MASK
    XOR STEPPER_GPIO_0, STEPPER_GPIO_0, r7
    SBBO STEPPER_GPIO_0, r0, 0, 4           // Clear the dirs

    // GPIO1
    MOV r0, GPIO1 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_1, r0, 0, 4
    MOV r0, GPIO1 | GPIO_CLEARDATAOUT
    MOV r7, GPIO1_DIR_MASK
    XOR STEPPER_GPIO_1, STEPPER_GPIO_1, r7
    SBBO STEPPER_GPIO_1, r0, 0, 4

    // GPIO2
    MOV r0, GPIO2 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_2, r0, 0, 4
    MOV r0, GPIO2 | GPIO_CLEARDATAOUT
    MOV r7, GPIO2_DIR_MASK
    XOR STEPPER_GPIO_2, STEPPER_GPIO_2, r7
    SBBO STEPPER_GPIO_2, r0, 0, 4

    // GPIO3
    MOV r0, GPIO3 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_3, r0, 0, 4
    MOV r0, GPIO3 | GPIO_CLEARDATAOUT
    MOV r7, GPIO3_DIR_MASK
    XOR STEPPER_GPIO_3, STEPPER_GPIO_3, r7
    SBBO STEPPER_GPIO_3, r0, 0, 4

    // Get the direction mask posted by PRU1. 
    // r7.b0 contains the mask for positive direction, (dir = 1)
    // and r7.b1 the mask for negative direction (dir = 0)
    LBCO r7, C28, 4, 4
    
    // After this, r7.b0 will have the positive mask for the step pins. 
    // If all steppers can move, the value of r7.b0 will be 0b11111111
    AND r7.b2, pinCommand.direction, r7.b1  // Build the mask for positive direction
    
    NOT r7.b3, pinCommand.direction         
    AND r7.b3, r7.b3, r7.b0                 // r7.b3 &= r7.b1  Build a mask for the negative direction

    OR  r7.b0, r7.b3, r7.b2                 // r7.b0 = r7.b3 | r7.b2

    //Check if we have to cancel the move based on the cancellableMask
    QBEQ notcancel, pinCommand.cancellableMask, 0

    //Check if we need to cancel the move, we have to if the mask doesn't match the allowed move
    AND r7.b1,pinCommand.cancellableMask,r7.b0    

    QBNE notcancel, r7.b1,0

    //Store the number of steps remaining
    ADD r22, r22, r1
    SBCO r22, C28, 16, 4

    //Remove all the command from the buffer
start_loop_remove:
    ADD  r4, r4, SIZE(SteppersCommand)
    SUB r1, r1, 1                                           // r1 contains the number of PIN instructions in the DDR, we remove one.
    QBNE start_loop_remove, r1, 0                           // Still more pins to go, jump back

    QBA CANCEL_COMMAND_AFTER

notcancel:
    MOV r22, 0                                              // Reset the Remaining steps loop
    SBCO r22, C28, 16, 4                                    // Store 0 to the shared memory
    
    AND r7, r7, 0x000000FF
    SBCO r7, C28, 12, 4
    AND pinCommand.step, pinCommand.step, r7.b0               // Mask the step pins with the end stop mask
 
    //Store the pins of the banks in registers
    MOV STEPPER_GPIO_0, 0
    MOV STEPPER_GPIO_1, 0
    MOV STEPPER_GPIO_2, 0
    MOV STEPPER_GPIO_3, 0
 
    //Stepper X 
    AND  r9,  pinCommand.step, 0x01 
    LSL  r9, r9, STEPPER_X_STEP_PIN 
    OR  STEPPER_X_STEP_BANK, STEPPER_X_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
 
    //Stepper Y 
    LSR  r9, pinCommand.step, 0x01 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_Y_STEP_PIN     
    OR  STEPPER_Y_STEP_BANK, STEPPER_Y_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
 
    //Stepper Z 
    LSR  r9, pinCommand.step, 0x02 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_Z_STEP_PIN     
    OR  STEPPER_Z_STEP_BANK, STEPPER_Z_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
 
    //Stepper E 
    LSR  r9, pinCommand.step, 0x03 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_E_STEP_PIN     
    OR  STEPPER_E_STEP_BANK, STEPPER_E_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
 
    //Stepper H 
    LSR  r9, pinCommand.step, 0x04 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_H_STEP_PIN     
    OR  STEPPER_H_STEP_BANK, STEPPER_H_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper

#ifdef STEPPER_A_DIR_BANK
    //Stepper A 
    LSR  r9, pinCommand.step, 0x05 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_A_STEP_PIN     
    OR  STEPPER_A_STEP_BANK, STEPPER_A_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper

    //Stepper B
    LSR  r9, pinCommand.step, 0x06 
    AND  r9, r9, 0x01 
    LSL  r9, r9, STEPPER_B_STEP_PIN     
    OR  STEPPER_B_STEP_BANK, STEPPER_B_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
#endif
#ifdef STEPPER_C_DIR_BANK
    //Stepper C
    LSR  r9, pinCommand.step, 0x07 
    AND  r9, r9, 0x01
    LSL  r9, r9, STEPPER_C_STEP_PIN     
    OR  STEPPER_C_STEP_BANK, STEPPER_C_STEP_BANK, r9        // Put a 1 into the GPIO value if we need to step this stepper
#endif

    // Minimum delay between setting direction and stepping
    // TODO: recalculate this! Get it from config file
    MOV r0,  55 //(660 - 22*CYCLE_TO_NS)*NS_TO_CYCLE/2

DELAY_SET:
    SUB r0, r0, 1
    QBNE DELAY_SET, r0, 0

    // Set step pins
    MOV r0, GPIO0 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_0, r0, 0, 4
    MOV r0, GPIO1 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_1, r0, 0, 4
    MOV r0, GPIO2 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_2, r0, 0, 4
    MOV r0, GPIO3 | GPIO_SETDATAOUT
    SBBO STEPPER_GPIO_3, r0, 0, 4

    //Increment reading address
    ADD  r4, r4, SIZE(SteppersCommand)

    //We have to wait 1.9us, minus the already spent time since the step is set up
    // TODO: recalculate this!  
    MOV r0, 190 //(1900 - 4*CYCLE_TO_NS)*NS_TO_CYCLE/2

DELAY_CLEAR:
    SUB r0, r0, 1
    QBNE DELAY_CLEAR, r0, 0

    // Clear step pins
    MOV r0, GPIO0 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_0, r0, 0, 4
    MOV r0, GPIO1 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_1, r0, 0, 4
    MOV r0, GPIO2 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_2, r0, 0, 4
    MOV r0, GPIO3 | GPIO_CLEARDATAOUT
    SBBO STEPPER_GPIO_3, r0, 0, 4

    //We need to have a min delay of 1.9us until the next steps
    MOV  r0, pinCommand.delay

    //559 INSTRUCTIONS UNTIL HERE, we have to wait 1.9us more before the next step

    //We substract the time to setup a step to the delay we need to wait as it is not counted by the host side
    MOV r9,559
    MAX r0,r0,r9
    SUB r0,r0,r9

    MOV r9,380 //(1900 - 3*CYCLE_TO_NS)*NS_TO_CYCLE 

    MAX  r0,r0, r9 

    //The delay is computed using two instructions ,we have to divide it by 2
    LSR r0,r0,1

    //Now execute the delay, with the proper substraction

DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0

    SUB r1, r1, 1                                           //r1 contains the number of stepper instructions in the DDR, we remove one.

SELFSUSPEND:
    QBBC SUSPENDED, pinCommand.options, 0                  // Check if this command requires syncronization
    QBBC SYNCHRONIZE, pinCommand.options, 1                // Check if this command also requires wait until sync cleared

    MOV r0, 1
    SBBO r0, r27, 0, 4                                      // Self-Suspend
    .leave CommandScope

SYNCHRONIZE:
    MOV R31.b0, PRU1_ARM_INTERRUPT	                        // Send sync event to Host

SUSPENDED:
    LBBO r0, r27, 0, 4                                      //Check if we are suspended or not
    QBNE SUSPENDED, r0, 0

    QBNE NEXT_COMMAND, r1, 0                                // Still more commands to go, jump back           
            
CANCEL_COMMAND_AFTER:           
            
    ADD r5, r5, 1                                           // r5++, r5 is the event_counter.
    SBBO r5, r6, 0, 4                                       // store the number of interrupts that have occured in the second reg of DRAM
    MOV R31.b0, PRU0_ARM_INTERRUPT		                    // Send notification to Host that the instructions are done
            
    MOV  r3, DDR_MAGIC                                      // Load the fancy word into r3
    LBBO r2, r4, 0, 4                                       // Load the next data into r2
    QBEQ RESET_R4, r2, r3                                   // Check if the end of DDR is reached
            
WAIT:           
    MOV  r3, DDR_MAGIC                                      // Load the fancy word into r3
WAIT2:
    LBBO r1, r4, 0, 4                                       // Load values from external DDR Memory into R1
    QBEQ RESET_R4, r1, r3                                   // Check if the end of DDR is reached   
    QBNE PINS, r1, 0                                        // Start to process the commands stored in DDR if we have a value != of 0 stored in the current location of the DDR    
    QBA WAIT2                                               // Loop back to wait for new data

