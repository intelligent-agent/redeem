.origin 0
.entrypoint INIT

//* CONFIGURATION SECTION */
//*************************/

//* PRU Register and constants */
#define PRU0_ARM_INTERRUPT              19
#define GPIO_DATAIN                     0x138                                   // This is the register for reading data 
#define GPIO0                           0x44E07000                              // The adress of the GPIO0 bank
#define GPIO1                           0x4804C000                              // The adress of the GPIO1 bank
#define GPIO2                           0x481AC000                              // The adress of the GPIO2 bank
#define GPIO3                           0x481AE000                              // The adress of the GPIO3 bank
#define PRU1_CONTROL_REGISTER_BASE      0x00024000                              //The base address for all the PRU1 control registers
#define CTPPR0_REGISTER                 PRU1_CONTROL_REGISTER_BASE + 0x28       //The CTPPR0 register for programming C28 and C29 entries
#define SHARED_RAM_ENDSTOPS_ADDR        0x0120

#define GPIO_0_IN r16
#define GPIO_1_IN r17
#define GPIO_2_IN r18
#define GPIO_3_IN r19

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
#error You must define the REV_A3 or REV_A4 preprocessor flag.
#endif


// Endstop/mask bit buildup: 0b00<Z+><Y+><X+><Z-><Y-><X->
// r7 : contains the endstop values 
// r9 : Contains the endstop inversion mask
// r8 : Contains the XYZ direction mask after lookup

//Memory map in shared RAM:
//0x0120:       Endstop state in the latest byte (0b00<Z+><Y+><X+><Z-><Y-><X->)    
//0x0124:       Direction mask produced by the endstops for negative direction    
//0x0125:       Direction mask produced by the endstops for positive direction

INIT:
    LBCO r0, C4, 4, 4              // Load the PRU-ICSS SYSCFG register (4 bytes) into R0
    CLR  r0, r0, 4                 // Clear bit 4 in reg 0 (copy of SYSCFG). This enables OCP master ports needed to access all OMAP peripherals
    SBCO r0, C4, 4, 4              // Load back the modified SYSCFG register    
    
    MOV  r0, SHARED_RAM_ENDSTOPS_ADDR                // Set the C28 address for shared ram, C29 is set to 0
    MOV  r1, CTPPR0_REGISTER
    SBBO r0, r1, 0, 4

    // Load inversion mask
    MOV r9, INVERSION_MASK          
    
    // Load lookup table
    //Config file syntax is  0b00<Z+><Y+><X+><Z-><Y-><X->
    //We need to produce 0x<DIRMAX><DIRMIN>
    MOV r10, STEPPER_MASK_X1 
    MOV r11, STEPPER_MASK_Y1
    MOV r12, STEPPER_MASK_Z1
    MOV r13, STEPPER_MASK_X2
    MOV r14, STEPPER_MASK_Y2
    MOV r15, STEPPER_MASK_Z2

    //Load GPIO0,1,2,3 read register content to the DDR
    MOV  r2, GPIO0 | GPIO_DATAIN
    MOV  r3, GPIO1 | GPIO_DATAIN
    MOV  r4, GPIO2 | GPIO_DATAIN
    MOV  r5, GPIO3 | GPIO_DATAIN

COLLECT: 

    //Read all GPIOs banks
    LBBO GPIO_0_IN, r2, 0, 4
    LBBO GPIO_1_IN, r3, 0, 4
    LBBO GPIO_2_IN, r4, 0, 4
    LBBO GPIO_3_IN, r5, 0, 4

    // Endstop X MIN
    LSR r0, STEPPER_X_END_MIN_BANK, STEPPER_X_END_MIN_PIN  // Right shift pin to bit 0
    AND r7,r0,0x01                                       // Endstop Xmin - Build a mask into r7.b0 that contains the end stop state. This will be used to mask the command.step field.

    // Endstop Y MIN
    LSR r0,STEPPER_Y_END_MIN_BANK,STEPPER_Y_END_MIN_PIN                         // Right shift the end stop pin to bit 0
    AND r0,r0,0x01                                          // Clear the other bits 
    LSL r0,r0,0x01                                          // Shift pin one left since it is Y
    OR r7,r7.b0,r0                                       // Mask away the step pin if the end stop is set

    // Endstop Z MIN              
    LSR r0,STEPPER_Z_END_MIN_BANK,STEPPER_Z_END_MIN_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x02
    OR  r7, r7,r0                                      

    // Endstop X MAX         
    LSR r0, STEPPER_X_END_MAX_BANK, STEPPER_X_END_MAX_PIN               
    AND r0,r0,0x01                                  
    LSL r0,r0,0x03
    OR  r7, r7,r0                                      

    // Endstop Y MAX              
    LSR r0,STEPPER_Y_END_MAX_BANK,STEPPER_Y_END_MAX_PIN                         
    AND r0,r0,0x01                                          
    LSL r0,r0,0x04                                          
    OR r7, r7 ,r0                                      

    // Endstop Z MAX               
    LSR r0,STEPPER_Z_END_MAX_BANK,STEPPER_Z_END_MAX_PIN
    AND r0,r0,0x01
    LSL r0,r0,0x05
    OR  r7, r7, r0

    // r9 has the invert mask for all endstops
    XOR r7, r7, r9

MASK:
    MOV r8, 0
MASK_X_MIN:
    QBBC MASK_Y_MIN, r7, 0                      // Jump to next label if bit 0 is clear 
    OR r8, r8, r10                     // Mask the stepper directions used by X_MIN
MASK_Y_MIN:
    QBBC MASK_Z_MIN, r7, 1
    OR r8, r8, r11
MASK_Z_MIN:
    QBBC MASK_X_MAX, r7, 2
    OR r8, r8, r12
MASK_X_MAX:
    QBBC MASK_Y_MAX, r7, 3
    OR r8, r8, r13
MASK_Y_MAX:
    QBBC MASK_Z_MAX, r7, 4
    OR r8, r8, r14
MASK_Z_MAX:
    QBBC PUBLISH, r7, 5
    OR r8, r8, r15

PUBLISH: 
    NOT r8.w0, r8.w0        //Invert so that the 1 (meaning do not move) becomes 0 for masking the step in PRU0
    SBCO r7, C28, 0, 8   // Publish the endstop states from r7/r8

    MOV r0, 200           // Add some delay
DELAY:
    SUB r0, r0, 1
    QBNE DELAY, r0, 0

    QBA COLLECT

