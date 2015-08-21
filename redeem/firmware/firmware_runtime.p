.origin 0
.entrypoint INIT

//* CONFIGURATION SECTION */
//*************************/

//* PRU Register and constants */
#define PRU_SPEED           200000000           //PRU clock speed in Hz - Should be 200'000'000 - IF YOU CHANGE IT YOU NEED TO RECOMPUTE ALL THE DELAYS.
#define CYCLE_TO_NS         1000000000/PRU_SPEED      //Number of cycles in 1 ns
#define NS_TO_CYCLE         PRU_SPEED/1000000000      //Number of ns in one cycle

#define PRU0_ARM_INTERRUPT  35
#define PRU1_ARM_INTERRUPT  36
#define GPIO_DATAOUT        0x13c               // This is the register for setting data 
#define GPIO_DATAIN         0x138               // This is the register for reading data 
#define GPIO0               0x44E07000          // The adress of the GPIO0 bank
#define GPIO1               0x4804C000          // The adress of the GPIO1 bank
#define GPIO2               0x481AC000          // The adress of the GPIO2 bank
#define GPIO3               0x481AE000          // The adress of the GPIO3 bank
#define PRU0_CONTROL_REGISTER_BASE      0x00022000                              //The base address for all the PRU1 control registers
#define CTPPR0_REGISTER                 PRU0_CONTROL_REGISTER_BASE + 0x28       //The CTPPR0 register for programming C28 and C29 entries
#define SHARED_RAM_ENDSTOPS_ADDR        0x0120

//* Magic number set by the host for DDR reset */
#define DDR_MAGIC           0xbabe7175          // Magic number used to reset the DDR counter 

#ifdef HAS_CONFIG_H
#include "config.h"
#endif

#ifdef REV_A3
#include "config_00A3.h"
#endif

#ifdef REV_A4
#include "config_00A4.h"
#endif

#ifdef REV_B2
#include "config_00B2.h"
#endif

#ifndef FIRMWARE_CONFIG
#error You must define the REV_A3 or REV_A4 preprocessor flag
#endif

//* Flag for generating proper code - DO NOT CHANGE
#define STEPPER_GPIO_0  r7
#define STEPPER_GPIO_1  r8

#define GPIO_0_IN r12
#define GPIO_1_IN r20
#define GPIO_2_IN r13
#define GPIO_3_IN r14

#define DIRECTION_MASK    ((STEPPER_H_DIRECTION << 4) | (STEPPER_E_DIRECTION << 3) | (STEPPER_Z_DIRECTION << 2) | (STEPPER_Y_DIRECTION << 1) | STEPPER_X_DIRECTION)


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


//We define a structure for commands send to the PRU and stored in DDR
.struct SteppersCommand
    .u8     step                //Steppers are defined as 0b000HEZYX - A 1 for a stepper means we will do a step for this stepper
    .u8     direction           //Steppers are defined as 0b000HEZYX - Direction for each stepper
    .u8     cancellableMask     //If the endstop match the mask, all the move commands are canceled. 
    .u8     options              //Options for the move, bit 0 indicates that a sync interrupt is required. bit 1 indicates that after the sync, suspend.
    .u32    delay               //number of cycle to wait (this is the # of PRU click cycles)
.ends


// Global register used:
//
// r1 : Remaining number of commands to process since we started to read DRAM
// r4 : Current command reading address in DRAM
// r5 : Event counter
// r6 : Address in DRAM where to put the events counter
// r7 :  
// r11: Adress for reading/writing GPIO0 OUT pins
// r12: GPIO0_IN
// r13: GPIO2_IN
// r14: GPIO_3_IN
// r15: Inverted mask for GPIO0 togglable pin
// r16: Inverted mask for GPIO1 togglable pin
// r17: Adress for reading/writing GPIO1 OUT pins
// r20: GPIO1_IN
// r22: Counts steps remaining

INIT:
    LBCO r0, C4, 4, 4                                       // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                                          // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4                                       // Load back the modified SYSCFG register
    
    MOV  r0, SHARED_RAM_ENDSTOPS_ADDR                       // Set the C28 address for shared ram, C29 is set to 0
    MOV  r1, CTPPR0_REGISTER
    SBBO r0, r1, 0, 4

    MOV  r17, GPIO1 | GPIO_DATAOUT                          // Load address for GPIO 1
    MOV  r16, 0xFFFFFFFF ^ (GPIO1_MASK)                     // Invert the mask for GPIO 1
    MOV  r11, GPIO0 | GPIO_DATAOUT                          // Load address for GPIO 0
    MOV  r15, 0xFFFFFFFF ^ (GPIO0_MASK)                     // Invert mask for GPIO 0
    
    MOV  r0, 4                                              // Load the address of the events_counter, written by the host system
    LBBO r6, r0, 0, 4                                       // Put it in R6
    MOV  r5, 0                                              // Make r5 the nr of events counter, 0 initially
    SBBO r5, r6, 0, 4                                       // store the number of interrupts that have occured in the second reg of DRAM

    MOV  r0, 8                                              // Load the address of the pru_control, written by the host system
    LBBO r27, r0, 0, 4                                      // Put it in R27
    
    //This parts read the GPIO IN Pins in all banks and return them to the hosts so that it can know the initial states of the end-stops.

    //Load GPIO0,1,2,3 read register content to the DDR
    MOV  r0, 0                                              // Address in DDR, starts at 0
    LBBO r2, r0, 0, 4   
    ADD  r2, r2, 4  
        
    MOV  GPIO_0_IN, GPIO0 | GPIO_DATAIN                     // Load Address
    LBBO r1, GPIO_0_IN, 0, 4                                // Read GPIO0 INPUT content
    SBBO r1, r2, 0, 4                                       // Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4  
    
    MOV  GPIO_1_IN, GPIO1 | GPIO_DATAIN                     // Load Address
    LBBO r1, GPIO_1_IN, 0, 4                                // Read GPIO1 INPUT content
    SBBO r1, r2, 0, 4                                       // Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4  
    
    MOV  GPIO_2_IN, GPIO2 | GPIO_DATAIN                     // Load Address
    LBBO r1, GPIO_2_IN, 0, 4                                // Read GPIO2 INPUT content
    SBBO r1, r2, 0, 4                                       // Put GPIO INPUT content into local RAM
    ADD  r2, r2, 4  
    
    MOV  GPIO_3_IN, GPIO3 | GPIO_DATAIN                      // Load Address
    LBBO r1, GPIO_3_IN, 0, 4                                 // Read GPIO3 INPUT content
    SBBO r1, r2, 0, 4                                        // Put GPIO INPUT content into local RAM
    
    //Set all the stepper pins to 0 
    
    LBBO r9, r11, 0,   4                                    // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                                   // Load pin data into r8 which is 4 bytes
    
    AND r9, r9, r15 
    AND r10, r10, r16   
    
    //Store back the value  
    SBBO r9, r11, 0, 4  
    SBBO r10, r17, 0, 4 
    
    MOV r22, 0

    //MOV R31.b0, PRU0_ARM_INTERRUPT	                    // Send notification to Host that the instructions are done
    
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

    //Translate the commands into pins
    //First load the direction pins

    //Store the pins of GPIO0 into r7 and GPIO1 into r8

    MOV r7, 0
    MOV r8, 0
    
    XOR r21,pinCommand.direction,DIRECTION_MASK          // Inverse the stepper direction mask
    AND r21,r21,0x1F

    //Stepper X
    AND  r9,  r21, 0x01
    LSL  r9, r9, STEPPER_X_DIR_PIN    
    OR  STEPPER_X_DIR_BANK, STEPPER_X_DIR_BANK, r9          // Put a 1/0 into the pin register for the stepper direction
    
    //Stepper Y     
    LSR  r9, r21, 0x01     
    AND  r9, r9, 0x01   
    LSL  r9, r9, STEPPER_Y_DIR_PIN      
    OR  STEPPER_Y_DIR_BANK, STEPPER_Y_DIR_BANK, r9          // Put a 1/0 into the pin register for the stepper direction
    
    //Stepper Z     
    LSR  r9, r21, 0x02     
    AND  r9, r9, 0x01   
    LSL  r9, r9, STEPPER_Z_DIR_PIN      
    OR  STEPPER_Z_DIR_BANK, STEPPER_Z_DIR_BANK, r9          // Put a 1/0 into the pin register for the stepper direction
    
    //Stepper E     
    LSR  r9, r21, 0x03     
    AND  r9, r9, 0x01   
    LSL  r9, r9, STEPPER_E_DIR_PIN      
    OR  STEPPER_E_DIR_BANK, STEPPER_E_DIR_BANK, r9          // Put a 1/0 into the pin register for the stepper direction
    
    //Stepper H     
    LSR  r9, r21, 0x04     
    AND  r9, r9, 0x01   
    LSL  r9, r9, STEPPER_H_DIR_PIN      
    OR  STEPPER_H_DIR_BANK, STEPPER_H_DIR_BANK, r9          // Put a 1/0 into the pin register for the stepper direction

    //Setup direction pin   
    LBBO r9, r11, 0,   4                                    // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                                   // Load pin data into r8 which is 4 bytes
    
    AND  r9, r9, r15                                        // Mask GPIO 0 and the pins
    AND  r10, r10, r16                                      // Mask GPIO 1 and the pins
    
    OR  r9, r9, r7                                          // Set the direction pin for GPIO 0
    OR  r10, r10, r8                                        // Set the direction pin for GPIO 1
    
    MOV r18,r7                                              // Save the value for future use - we will need this value for the step pins
    MOV r19,r8                                              // Save the value for future use - we will need this value for the step pins
    
    //Store back the value  
    SBBO r9, r11, 0, 4                                      // Trigger the change of the steppers direction pins (GPIO 0)
    SBBO r10, r17, 0, 4                                     // Trigger the change of the steppers direction pins (GPIO 1)

    //33 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND

    // Get the direction mask posted by PRU1. 
    // r7.b0 contains the mask for positive direction, (dir = 1)
    // and r7.b1 the mask for negative direction (dir = 0)
    LBCO r7, C28, 4, 4
    
    // After this, r7.b0 will have the positive mask for the step pins. 
    // If all steppers can move, the value of r7.b0 will be 0b00011111
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
    SBCO r22, C28, 12, 4

    //Remove all the command from the buffer
start_loop_remove:
    ADD  r4, r4, SIZE(SteppersCommand)
    SUB r1, r1, 1                                           // r1 contains the number of PIN instructions in the DDR, we remove one.
    QBNE start_loop_remove, r1, 0                           // Still more pins to go, jump back

    QBA CANCEL_COMMAND_AFTER

notcancel:
    MOV r22, 0                                              // Reset the Remaining-loop

    AND r7, r7, 0x000000FF
    SBCO r7, C28, 8, 4
    AND pinCommand.step, pinCommand.step, r7.b0               // Mask the step pins with the end stop mask
 
    //Build the step pins GPIOs values 
    MOV r7, 0 
    MOV r8, 0 
 
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


    
    OR r7,r7,r18                                            // Add directions for GPIO 0 that we saved before
    OR r8,r8,r19                                            // Add directions for GPIO 1 that we saved before

    //55 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND
    //22 instructions since the direction command
 
    //We have to wait 660 ns between the direction pin setup and the step pin setup
    //PASM is super buggy so it cannot evaluate it. Hardcoding the value here.

    MOV r0,  55 //(660 - 22*CYCLE_TO_NS)*NS_TO_CYCLE/2

DELAY3:
    SUB r0, r0, 1
    QBNE DELAY3, r0, 0

    //165 INSTRUCTIONS UNTIL HERE SINCE THE START OF THE STEP COMMAND

    //Setup step pin
    LBBO r9, r11, 0,   4                                    // Load pin data into r7 which is 4 bytes
    LBBO r10, r17, 0,   4                                   // Load pin data into r8 which is 4 bytes

    AND  r9, r9, r15 //Set GPIO 0 for step pin
    AND  r10, r10, r16 //Set GPIO 1 for step pin

    OR  r9, r9, r7 //Set GPIO 0 for step pin
    OR  r10, r10, r8 //Set GPIO 1 for step pin

    //Store back the value for step pins
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

    AND r9, r9, r15                                         // Prepare the step pins to 0 to store it just after the delay
    AND r10, r10, r16                                       // Prepare the step pins to 0 to store it just after the delay

    //Increment reading address
    ADD  r4, r4, SIZE(SteppersCommand)

    //176 INSTRUCTIONS UNTIL HERE

    //We have to wait 1.9us, minus the already spent time since the step is set up

    MOV r0, 190 //(1900 - 4*CYCLE_TO_NS)*NS_TO_CYCLE/2
DELAY2:
    SUB r0, r0, 1
    QBNE DELAY2, r0, 0

    //put all the step pin to low from the prepared values
    SBBO r9, r11, 0, 4
    SBBO r10, r17, 0, 4

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

    MOV R31.b0, PRU1_ARM_INTERRUPT	                    // Send sync event to Host

SUSPENDED:
    LBBO r0, r27, 0, 4                                      //Check if we are suspended or not
    QBNE SUSPENDED, r0, 0

    QBNE NEXT_COMMAND, r1, 0                                // Still more commands to go, jump back           
            
CANCEL_COMMAND_AFTER:           
            
    ADD r5, r5, 1                                           // r5++, r5 is the event_counter.
    SBBO r5, r6, 0, 4                                       // store the number of interrupts that have occured in the second reg of DRAM
    MOV R31.b0, PRU0_ARM_INTERRUPT		            // Send notification to Host that the instructions are done
            
    MOV  r3, DDR_MAGIC                                      // Load the fancy word into r3
    LBBO r2, r4, 0, 4                                       // Load the next data into r2
    QBEQ RESET_R4, r2, r3                                   // Check if the end of DDR is reached
            
            
WAIT:           
    MOV  r3, DDR_MAGIC                                      // Load the fancy word into r3
WAIT2:
    LBBO r1, r4, 0, 4                                       // Load values from external DDR Memory into R1
    QBEQ RESET_R4, r1, r3                                   // Check if the end of DDR is reached   
    QBNE PINS, r1, 0                                        // Start to process the commands stored in DDR if we have a value != of 0 stored in the current location of the DDR    
    QBA WAIT2                                                // Loop back to wait for new data

