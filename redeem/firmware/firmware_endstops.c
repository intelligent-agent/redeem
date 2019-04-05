#include <stdint.h>
#include <pru_cfg.h>
#include <pru_ctrl.h>

#include "config.h"

//* Constants */
#define GPIO_DATAIN 0x138 // This is the register for reading data
#define GPIO0 0x44E07000 // The address of the GPIO0 bank
#define GPIO1 0x4804C000 // The address of the GPIO1 bank
#define GPIO2 0x481AC000 // The address of the GPIO2 bank
#define GPIO3 0x481AE000 // The address of the GPIO3 bank
#define SHARED_RAM_ENDSTOPS_ADDR 0x0120

#include "config.h"

#define GPIO_0_IN gpio0
#define GPIO_1_IN gpio1
#define GPIO_2_IN gpio2
#define GPIO_3_IN gpio3

volatile uint32_t* const GPIO0_DATAIN = (uint32_t*)(GPIO0 | GPIO_DATAIN);
volatile uint32_t* const GPIO1_DATAIN = (uint32_t*)(GPIO1 | GPIO_DATAIN);
volatile uint32_t* const GPIO2_DATAIN = (uint32_t*)(GPIO2 | GPIO_DATAIN);
volatile uint32_t* const GPIO3_DATAIN = (uint32_t*)(GPIO3 | GPIO_DATAIN);

// TODO in theory, this should put a uint32_t at the start of the block of memory
// pointed to by C28, but TI doesn't promise any particular placement.
// Is there a way to get that guarantee?
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_endstopState;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_stepperMask;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_endstopActiveState;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_steppersAllowedToMove;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_stepsRemaining;

inline void delay(uint32_t until)
{
    while (PRU1_CTRL.CYCLE < until)
        ;
}

int main(void)
{
    // Initialization
    CT_CFG.SYSCFG_bit.STANDBY_INIT = 0;
    PRU1_CTRL.CTPPR0_bit.C28_BLK_POINTER = SHARED_RAM_ENDSTOPS_ADDR;

    while (1)
    {
        // Reset the cycle counter - it stops itself once it reaches 0xFFFFFFFF instead of wrapping around,
        // so we need to reset it for each loop ieration to be sure it'll be working.
        // (Otherwise it'll stop after 0xFFFFFFFF / 200MHz = 21.5 seconds)
        PRU1_CTRL.CTRL_bit.CTR_EN = 0; // Disable counter
        PRU1_CTRL.CYCLE = 0; // Zero counter
        PRU1_CTRL.CTRL_bit.CTR_EN = 1; // Enable counter

        uint32_t gpio0 = *GPIO0_DATAIN;
        uint32_t gpio1 = *GPIO1_DATAIN;
        uint32_t gpio2 = *GPIO2_DATAIN;
        uint32_t gpio3 = *GPIO3_DATAIN;

        uint32_t state = 0;
        state |= ((STEPPER_X1_END_BANK >> STEPPER_X1_END_PIN) & 0x1) << 0;
        state |= ((STEPPER_Y1_END_BANK >> STEPPER_Y1_END_PIN) & 0x1) << 1;
        state |= ((STEPPER_Z1_END_BANK >> STEPPER_Z1_END_PIN) & 0x1) << 2;
        state |= ((STEPPER_X2_END_BANK >> STEPPER_X2_END_PIN) & 0x1) << 3;
        state |= ((STEPPER_Y2_END_BANK >> STEPPER_Y2_END_PIN) & 0x1) << 4;
        state |= ((STEPPER_Z2_END_BANK >> STEPPER_Z2_END_PIN) & 0x1) << 5;

        state ^= INVERSION_MASK;
        state &= g_endstopActiveState;

        uint32_t stepperMask = 0;
        if ((state >> 0) & 1)
        {
            stepperMask |= STEPPER_MASK_X1;
        }
        if ((state >> 1) & 1)
        {
            stepperMask |= STEPPER_MASK_Y1;
        }
        if ((state >> 2) & 1)
        {
            stepperMask |= STEPPER_MASK_Z1;
        }
        if ((state >> 3) & 1)
        {
            stepperMask |= STEPPER_MASK_X2;
        }
        if ((state >> 4) & 1)
        {
            stepperMask |= STEPPER_MASK_Y2;
        }
        if ((state >> 5) & 1)
        {
            stepperMask |= STEPPER_MASK_Z2;
        }

        stepperMask = ~stepperMask; // Invert from a set of motors we should mask to a set of motors that are allowed to move

        g_endstopState = state;
        g_stepperMask = stepperMask;

        delay(END_STOP_DELAY);
    }
}
