.origin 0
.entrypoint INIT

//* CONFIGURATION SECTION */
//*************************/

//* PRU Register and constants */
#define PRU0_ARM_INTERRUPT  19
#define GPIO_DATAIN         0x138               // This is the register for reading data 
#define GPIO0               0x44E07000          // The adress of the GPIO0 bank
#define GPIO1               0x4804C000          // The adress of the GPIO1 bank
#define GPIO2               0x481AC000          // The adress of the GPIO2 bank
#define GPIO3               0x481AE000          // The adress of the GPIO3 bank

#define GPIO_0_IN r12
#define GPIO_1_IN r20
#define GPIO_2_IN r13
#define GPIO_3_IN r14

#ifdef REV_A3
#include "config_00A3.h"
#endif

#ifdef REV_A4
#include "config_00A4.h"
#endif

#ifndef FIRMWARE_CONFIG
#error You must define the REV_A3 or REV_A4 preprocessor flag
#endif

#define MASK_PUBLISH_ADDR   0x00010000 // The address to store the mask in local shared ram. 
#define STEPPER_INVERT_ADDR 0x00000000 // Where to get the inversion mask
#define STEPPER_LOOKUP_ADDR 0x00000004 // Where to get the lookup table

#define MIN_X_STEPPER_MASK  0b00000011 // If X_MIN is hit, stop X- and Y-
#define MIN_Y_STEPPER_MASK  0b00001001 // If Y_MIN is hit, stop X- and Y+
#define MIN_Z_STEPPER_MASK  0b00000100 // If Z_MIN is hit, stop Z-
#define MAX_X_STEPPER_MASK  0b00011000 // If X_MAX is hit, stop X+ and Y+
#define MAX_Y_STEPPER_MASK  0b00001010 // If Y_MAX is hit, stop X+ and Y-
#define MAX_Z_STEPPER_MASK  0b00100000 // If Z_MAX is hit, stop Z+


// Endstop/mask bit buildup: 0b00<Z+><Y+><X+><Z-><Y-><X->
// r6    : Stepper invert mask
// r7.b0 : contains the endstop values 
// r8.b0 : Contains the endstop inversion mask
// r9.b0 : Contains the direction mask after lookup


INIT:
    LBCO r0, C4, 4, 4                                       // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                                          // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4                                       // Load back the modified SYSCFG register    
    

    // Load the values into local mem. This is just for debugging
    MOV r0, STEPPER_INVERT_ADDR
    MOV r1, 0x00000000
    SBBO r0, r1, 0, 4
    
    MOV r0, STEPPER_LOOKUP_ADDR
    MOV r10, MIN_X_STEPPER_MASK
    MOV r11, MIN_Y_STEPPER_MASK
    MOV r12, MIN_Z_STEPPER_MASK
    MOV r13, MAX_X_STEPPER_MASK
    MOV r14, MAX_Y_STEPPER_MASK
    MOV r15, MAX_Z_STEPPER_MASK
    SBBO r0, r10, 0, 24 
    // Done debug

    MOV  r0, STEPPER_INVERT_ADDR                            // Load the endstop inversion mask
    LBBO r8, r0, 0, 4   
    
    MOV r0, STEPPER_LOOKUP_ADDR                             // Load the stepper lookup table, 6*4 bytes
    LBBO r10, r0, 0, 24

    //Load GPIO0,1,2,3 read register content to the DDR
    MOV  GPIO_0_IN, GPIO0 | GPIO_DATAIN                     // Load Address
    MOV  GPIO_1_IN, GPIO1 | GPIO_DATAIN                     // Load Address
    MOV  GPIO_2_IN, GPIO2 | GPIO_DATAIN                     // Load Address
    MOV  GPIO_3_IN, GPIO3 | GPIO_DATAIN                     // Load Address

COLLECT: 
    // Endstop X MIN
    LBBO r0, STEPPER_X_END_MIN_BANK, 0, 4                   // Read the GPIO bank
    LSR r0, r0, STEPPER_X_END_MIN_PIN                       // Right shift pin to bit 0
    AND r7.b0,r0,0x01                                       // Endstop Xmin - Build a mask into r7.b0 that contains the end stop state. This will be used to mask the command.step field.

    // Endstop Y MIN
    LBBO r0, STEPPER_Y_END_MIN_BANK, 0, 4                   // Read the GPIO bank
    LSR r0,r0,STEPPER_Y_END_MIN_PIN                         // Right shift the end stop pin to bit 0
    AND r0,r0,0x01                                          // Clear the other bits 
    LSL r0,r0,0x01                                          // Shift pin one left since it is Y
    OR r7.b0,r7.b0,r0                                       // Mask away the step pin if the end stop is set

    // Endstop Z MIN
    LBBO r0, STEPPER_Z_END_MIN_BANK, 0, 4                   
    LSR r0,r0,STEPPER_Z_END_MIN_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x02
    OR  r7.b0,r7.b0,r0                                      

    // Endstop X MAX
    LBBO r0, STEPPER_X_END_MAX_BANK, 0, 4           
    LSR r0, r0, STEPPER_X_END_MAX_PIN               
    AND r0,r0,0x01                                  
    LSL r0,r0,0x03
    OR  r7.b0,r7.b0,r0                                      

    // Endstop Y MAX 
    LBBO r0, STEPPER_Y_END_MAX_BANK, 0, 4                   
    LSR r0,r0,STEPPER_Y_END_MAX_PIN                         
    AND r0,r0,0x01                                          
    LSL r0,r0,0x04                                          
    OR r7.b0,r7.b0,r0                                      

    // Endstop Z MAX
    LBBO r0, STEPPER_Z_END_MIN_BANK, 0, 4                  
    LSR r0,r0,STEPPER_Z_END_MIN_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x05
    OR  r7.b0,r7.b0,r0

    // r8.b0 has the invert mask for all endstops
    XOR r7.b0, r7.b0, r8.b0

MASK:
    MOV r9, 0
MASK_X_MIN:
    QBBC MASK_Y_MIN, r7.b0, 0               // Jump to next label if bit 0 is clear 
    OR r9, r9, r10                          // Mask the stepper directions used by X_MIN
MASK_Y_MIN:
    QBBC MASK_Z_MIN, r7.b0, 1
    OR r9, r9, r11
MASK_Z_MIN:
    QBBC MASK_X_MAX, r7.b0, 2
    OR r9, r9, r12
MASK_X_MAX:
    QBBC MASK_Y_MAX, r7.b0, 3
    OR r9, r9, r13
MASK_Y_MAX:
    QBBC MASK_Z_MAX, r7.b0, 4
    OR r9, r9, r14
MASK_Z_MAX:
    QBBC PUBLISH, r7.b0, 5
    OR r9, r9, r15

PUBLISH: 
    MOV  r0, MASK_PUBLISH_ADDR              // Publish the available directions for the steppers to the shared RAM
    SBBO r9, r0, 0, 4 
    QBA COLLECT
    

