#include <stdint.h>
#include <pru_cfg.h>
#include <pru_ctrl.h>

#include "config.h"

//* Constants */

#define PRU0_ARM_INTERRUPT 35
#define PRU1_ARM_INTERRUPT 36
#define SHARED_RAM_ENDSTOPS_ADDR 0x0120

//* Magic number set by the host for DDR reset */
#define DDR_MAGIC 0xbabe7175 // Magic number used to reset the DDR counter

#define STEPPER_GPIO_0 gpio0
#define STEPPER_GPIO_1 gpio1
#define STEPPER_GPIO_2 gpio2
#define STEPPER_GPIO_3 gpio3

volatile uint32_t* const GPIO0_DATAOUT = (uint32_t*)0x44E0713c;
volatile uint32_t* const GPIO1_DATAOUT = (uint32_t*)0x4804C13c;
volatile uint32_t* const GPIO2_DATAOUT = (uint32_t*)0x481AC13c;
volatile uint32_t* const GPIO3_DATAOUT = (uint32_t*)0x481AE13c;
volatile uint32_t* const GPIO0_CLEARDATAOUT = (uint32_t*)0x44E07190;
volatile uint32_t* const GPIO1_CLEARDATAOUT = (uint32_t*)0x4804C190;
volatile uint32_t* const GPIO2_CLEARDATAOUT = (uint32_t*)0x481AC190;
volatile uint32_t* const GPIO3_CLEARDATAOUT = (uint32_t*)0x481AE190;
volatile uint32_t* const GPIO0_SETDATAOUT = (uint32_t*)0x44E07194;
volatile uint32_t* const GPIO1_SETDATAOUT = (uint32_t*)0x4804C194;
volatile uint32_t* const GPIO2_SETDATAOUT = (uint32_t*)0x481AC194;
volatile uint32_t* const GPIO3_SETDATAOUT = (uint32_t*)0x481AE194;

// TODO in theory, this should put a uint32_t at the start of the block of memory
// pointed to by C28, but TI doesn't promise any particular placement.
// Is there a way to get that guarantee?
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_endstopState;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_stepperMask;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_unused2;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_steppersAllowedToMove;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_stepsRemaining;
__far __attribute__((cregister("PRU_SHAREDMEM", near))) volatile uint32_t g_endstops_triggered;

typedef struct SteppersCommand
{
    uint8_t step;
    uint8_t direction;
    uint8_t cancellableMask;
    uint8_t options;
    uint32_t delay;
} SteppersCommand;

inline void delay(uint32_t until)
{
    while (PRU0_CTRL.CYCLE < until)
        ;
}

inline void armPru0Interrupt()
{
    __asm("        LDI       r31.b0, 35"); // PRU0_ARM_INTERRUPT
}

inline void armPru1Interrupt()
{
    __asm("        LDI       r31.b0, 36"); // PRU1_ARM_INTERRUPT
}

int main(void)
{
    // Initialization
    CT_CFG.SYSCFG_bit.STANDBY_INIT = 0;
    PRU0_CTRL.CTPPR0_bit.C28_BLK_POINTER = SHARED_RAM_ENDSTOPS_ADDR;

    volatile uint32_t* const events_counter = *((uint32_t**)0x4);
    volatile uint32_t* const pru_control = *((uint32_t**)0x8);
    volatile uint32_t** const ddr_start = (volatile uint32_t**)0; // because dereferencing null is fun!

    uint32_t gpio0 = GPIO0_MASK;
    uint32_t gpio1 = GPIO1_MASK;
    uint32_t gpio2 = GPIO2_MASK;
    uint32_t gpio3 = GPIO3_MASK;

    uint32_t carriedBlockedSteppers = 0;

    *GPIO0_CLEARDATAOUT = gpio0;
    *GPIO1_CLEARDATAOUT = gpio1;
    *GPIO2_CLEARDATAOUT = gpio2;
    *GPIO3_CLEARDATAOUT = gpio3;

    g_stepsRemaining = 0;

    while (1)
    {
        volatile uint32_t* ddr_addr = *ddr_start;

        while (*ddr_addr != DDR_MAGIC)
        {

            while (*ddr_addr == 0)
            {
            }

            uint32_t numCommands = *ddr_addr;
            SteppersCommand* curCommand = (SteppersCommand*)(ddr_addr + 1);

            if(!(curCommand->options & 0x04))
            {
                // don't carry blocked steppers
                carriedBlockedSteppers = 0;
            }

            while (numCommands)
            {
                // Reset the cycle counter - it stops itself once it reaches 0xFFFFFFFF instead of wrapping around,
                // so we need to reset it for each command to be sure it'll be working.
                // (Otherwise it'll stop after 0xFFFFFFFF / 200MHz = 21.5 seconds)
                PRU0_CTRL.CTRL_bit.CTR_EN = 0; // Disable counter
                PRU0_CTRL.CYCLE = 0; // Zero counter
                PRU0_CTRL.CTRL_bit.CTR_EN = 1; // Enable counter

                // Handle steppers that have been inverted in the config
                uint8_t direction = (curCommand->direction ^ DIRECTION_MASK) & 0xFF;

                gpio0 = gpio1 = gpio2 = gpio3 = 0;

                STEPPER_X_DIR_BANK |= ((direction >> 0) & 0x01) << STEPPER_X_DIR_PIN;
                STEPPER_Y_DIR_BANK |= ((direction >> 1) & 0x01) << STEPPER_Y_DIR_PIN;
                STEPPER_Z_DIR_BANK |= ((direction >> 2) & 0x01) << STEPPER_Z_DIR_PIN;
                STEPPER_E_DIR_BANK |= ((direction >> 3) & 0x01) << STEPPER_E_DIR_PIN;
                STEPPER_H_DIR_BANK |= ((direction >> 4) & 0x01) << STEPPER_H_DIR_PIN;
#ifdef STEPPER_A_DIR_BANK
                STEPPER_A_DIR_BANK |= ((direction >> 5) & 0x01) << STEPPER_A_DIR_PIN;
#endif
#ifdef STEPPER_B_DIR_BANK
                STEPPER_B_DIR_BANK |= ((direction >> 6) & 0x01) << STEPPER_B_DIR_PIN;
#endif
#ifdef STEPPER_C_DIR_BANK
                STEPPER_C_DIR_BANK |= ((direction >> 7) & 0x01) << STEPPER_C_DIR_PIN;
#endif

                *GPIO0_SETDATAOUT = gpio0; // set the directions we need
                *GPIO0_CLEARDATAOUT = gpio0 ^ GPIO0_DIR_MASK; // clear the directions we control but don't currently need

                *GPIO1_SETDATAOUT = gpio1;
                *GPIO1_CLEARDATAOUT = gpio1 ^ GPIO1_DIR_MASK;

                *GPIO2_SETDATAOUT = gpio2;
                *GPIO2_CLEARDATAOUT = gpio2 ^ GPIO2_DIR_MASK;

                *GPIO3_SETDATAOUT = gpio3;
                *GPIO3_CLEARDATAOUT = gpio3 ^ GPIO3_DIR_MASK;

                const uint32_t dirSetTime = PRU0_CTRL.CYCLE;

                const uint32_t directionsAllowedMask = g_stepperMask & ~carriedBlockedSteppers;
                const uint8_t positiveDirectionsAllowed = curCommand->direction & ((directionsAllowedMask >> 8) & 0xFF);
                const uint8_t negativeDirectionsAllowed = ~curCommand->direction & (directionsAllowedMask & 0xFF);
                const uint8_t allDirectionsAllowed = positiveDirectionsAllowed | negativeDirectionsAllowed;

                if (curCommand->options & 0x04)
                {
                    carriedBlockedSteppers |= ~directionsAllowedMask;
                }

                if (curCommand->cancellableMask != 0
                    && (allDirectionsAllowed & curCommand->cancellableMask) == 0)
                {
                    // All of the steppers in cancellableMask aren't allowed to move - this means
                    // we need to cancel the move.
                    g_stepsRemaining += numCommands;
                    curCommand += numCommands;
                    numCommands = 0;

                    (*events_counter)++;
                    __asm("        LDI       R31.b0, 35"); // PRU0_ARM_INTERRUPT

                    // Copy this pointer back so we can check it for DDR_MAGIC
                    ddr_addr = (uint32_t*)curCommand;
                    break;
                }
                else if (curCommand->cancellableMask == 0
                    && (allDirectionsAllowed & curCommand->step) != curCommand->step)
                {
                    // This move isn't cancellable, but one or more of its axes are blocked.
                    // Stop immediately and sound the alarm.
                    *events_counter = 0xFFFFFFFF;
                    g_endstops_triggered = g_endstopState;
                    armPru0Interrupt();

                    // Don't allow recovery - we have some unknown number of steps already queued up.
                    // Just wait for the host to reset the whole PRU.
                    while (1)
                    {
                    }
                }

                // TODO This is carried over from the original assembly, but it's unclear
                // whether it's actually used anywhere.
                g_steppersAllowedToMove = allDirectionsAllowed;

                uint8_t steps = curCommand->step & allDirectionsAllowed;

                gpio0 = gpio1 = gpio2 = gpio3 = 0;

                STEPPER_X_STEP_BANK |= ((steps >> 0) & 0x01) << STEPPER_X_STEP_PIN;
                STEPPER_Y_STEP_BANK |= ((steps >> 1) & 0x01) << STEPPER_Y_STEP_PIN;
                STEPPER_Z_STEP_BANK |= ((steps >> 2) & 0x01) << STEPPER_Z_STEP_PIN;
                STEPPER_E_STEP_BANK |= ((steps >> 3) & 0x01) << STEPPER_E_STEP_PIN;
                STEPPER_H_STEP_BANK |= ((steps >> 4) & 0x01) << STEPPER_H_STEP_PIN;
#ifdef STEPPER_A_STEP_BANK
                STEPPER_A_STEP_BANK |= ((steps >> 5) & 0x01) << STEPPER_A_STEP_PIN;
#endif
#ifdef STEPPER_B_STEP_BANK
                STEPPER_B_STEP_BANK |= ((steps >> 6) & 0x01) << STEPPER_B_STEP_PIN;
#endif
#ifdef STEPPER_C_STEP_BANK
                STEPPER_C_STEP_BANK |= ((steps >> 7) & 0x01) << STEPPER_C_STEP_PIN;
#endif

                // We may need to wait before stepping - if we don't, this will be a no-op
                delay(dirSetTime + DELAY_BETWEEN_DIR_AND_STEP);

                *GPIO0_SETDATAOUT = gpio0;
                *GPIO1_SETDATAOUT = gpio1;
                *GPIO2_SETDATAOUT = gpio2;
                *GPIO3_SETDATAOUT = gpio3;

                // We definitely need to wait before we clear the step pins
                delay(PRU0_CTRL.CYCLE + DELAY_BETWEEN_STEP_AND_CLEAR);

                *GPIO0_CLEARDATAOUT = gpio0;
                *GPIO1_CLEARDATAOUT = gpio1;
                *GPIO2_CLEARDATAOUT = gpio2;
                *GPIO3_CLEARDATAOUT = gpio3;

                // Conveniently, we reset the timer at the start of this step. This means that exactly PRU0_CTRL.CYCLE
                // cycles have elapsed since we started. If we wait until curCommand->delay cycles have elapsed, this step
                // will be the right length. It may need to be longer to meet the minimum delay, however.

                const uint32_t minimumWait = PRU0_CTRL.CYCLE + MINIMUM_DELAY_AFTER_STEP;

                delay(minimumWait > curCommand->delay ? minimumWait : curCommand->delay);

                numCommands--;
                curCommand++;

                if (curCommand->options & 0x01) // synchronize
                {
                    if (curCommand->options & 0x02) // synchronize and suspend
                    {
                        *pru_control = 1;
                    }

                    armPru1Interrupt();
                }

                while (*pru_control != 0)
                {
                }
            }

            (*events_counter)++;

            armPru0Interrupt();

            // Copy this pointer back so we can check it for DDR_MAGIC
            ddr_addr = (uint32_t*)curCommand;
        }
    }
}
