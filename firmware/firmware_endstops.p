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

#define GPIO_0_IN r16
#define GPIO_1_IN r17
#define GPIO_2_IN r18
#define GPIO_3_IN r19

#ifdef REV_A3
#include "config_00A3.h"
#endif

#ifdef REV_A4
#include "config_00A4.h"
#endif

#ifndef FIRMWARE_CONFIG
#warning You must define the REV_A3 or REV_A4 preprocessor flag. Using default values.

#define STEPPER_MASK_X1  0x0003 // If X_MIN is hit, stop X- and Y-
#define STEPPER_MASK_Y1  0x0201 // If Y_MIN is hit, stop X- and Y+
#define STEPPER_MASK_Z1  0x0004 // If Z_MIN is hit, stop Z-
#define STEPPER_MASK_X2  0x0300 // If X_MAX is hit, stop X+ and Y+
#define STEPPER_MASK_Y2  0x0102 // If Y_MAX is hit, stop X+ and Y-
#define STEPPER_MASK_Z2  0x0400 // If Z_MAX is hit, stop Z+

#define INVERSION_MASK   0b00111111 // Which endstops to invert

#endif


// Endstop/mask bit buildup: 0b00<Z+><Y+><X+><Z-><Y-><X->
// r7 : contains the endstop values 
// r8 : Contains the endstop inversion mask
// r9 : Contains the XYZ direction mask after lookup



INIT:
    LBCO r0, C4, 4, 4              // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                 // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4              // Load back the modified SYSCFG register    
    
    MOV  r0, 0x0120                // Set the C28 address for shared ram
    MOV  r1, 0x00024028
    SBBO r0, r1, 0, 4

    // Load inversion mask
    MOV r8, INVERSION_MASK          
    
    // Load lookup table
    MOV r10, STEPPER_MASK_X1     
    MOV r11, STEPPER_MASK_Y1
    MOV r12, STEPPER_MASK_Z1
    MOV r13, STEPPER_MASK_X2
    MOV r14, STEPPER_MASK_Y2
    MOV r15, STEPPER_MASK_Z2

    //Load GPIO0,1,2,3 read register content to the DDR
    MOV  GPIO_0_IN, GPIO0 | GPIO_DATAIN
    MOV  GPIO_1_IN, GPIO1 | GPIO_DATAIN
    MOV  GPIO_2_IN, GPIO2 | GPIO_DATAIN
    MOV  GPIO_3_IN, GPIO3 | GPIO_DATAIN

COLLECT: 
    // Endstop X MIN
    LBBO r0, STEPPER_X_END_MIN_BANK, 0, 4                   // Read the GPIO bank
    LSR r0, r0, STEPPER_X_END_MIN_PIN                       // Right shift pin to bit 0
    AND r7,r0,0x01                                       // Endstop Xmin - Build a mask into r7.b0 that contains the end stop state. This will be used to mask the command.step field.

    // Endstop Y MIN
    LBBO r0, STEPPER_Y_END_MIN_BANK, 0, 4                   // Read the GPIO bank
    LSR r0,r0,STEPPER_Y_END_MIN_PIN                         // Right shift the end stop pin to bit 0
    AND r0,r0,0x01                                          // Clear the other bits 
    LSL r0,r0,0x01                                          // Shift pin one left since it is Y
    OR r7,r7.b0,r0                                       // Mask away the step pin if the end stop is set

    // Endstop Z MIN
    LBBO r0, STEPPER_Z_END_MIN_BANK, 0, 4                   
    LSR r0,r0,STEPPER_Z_END_MIN_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x02
    OR  r7, r7,r0                                      

    // Endstop X MAX
    LBBO r0, STEPPER_X_END_MAX_BANK, 0, 4           
    LSR r0, r0, STEPPER_X_END_MAX_PIN               
    AND r0,r0,0x01                                  
    LSL r0,r0,0x03
    OR  r7, r7,r0                                      

    // Endstop Y MAX 
    LBBO r0, STEPPER_Y_END_MAX_BANK, 0, 4                   
    LSR r0,r0,STEPPER_Y_END_MAX_PIN                         
    AND r0,r0,0x01                                          
    LSL r0,r0,0x04                                          
    OR r7, r7 ,r0                                      

    // Endstop Z MAX
    LBBO r0, STEPPER_Z_END_MIN_BANK, 0, 4                  
    LSR r0,r0,STEPPER_Z_END_MIN_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x05
    OR  r7, r7, r0

    // r8 has the invert mask for all endstops
    XOR r7, r7, r8

MASK:
    MOV r9, 0
MASK_X_MIN:
    QBBC MASK_Y_MIN, r7, 0                      // Jump to next label if bit 0 is clear 
    OR r9, r9, r10                     // Mask the stepper directions used by X_MIN
MASK_Y_MIN:
    QBBC MASK_Z_MIN, r7, 1
    OR r9, r9, r11
MASK_Z_MIN:
    QBBC MASK_X_MAX, r7, 2
    OR r9, r9, r12
MASK_X_MAX:
    QBBC MASK_Y_MAX, r7, 3
    OR r9, r9, r13
MASK_Y_MAX:
    QBBC MASK_Z_MAX, r7, 4
    OR r9, r9, r14
MASK_Z_MAX:
    QBBC PUBLISH, r7, 5
    OR r9, r9, r15

PUBLISH: 
    NOT r9.w0, r9.w0
    SBCO r7, c28, 0, 12   // Publish the endstop states
    QBA COLLECT

