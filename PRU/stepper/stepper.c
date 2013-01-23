#include <stdio.h>

#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define PRU_NUM 0
#define AM33XX
#define NUM_COMMANDS 10
#define NUM_DELAYS 10

int main (void)
{
	int i;
    unsigned int ret;
	unsigned int delays[NUM_DELAYS];
	unsigned int commands[NUM_COMMANDS];
	for(i=0; i<NUM_DELAYS; i++)
		delays[i] = 0x00F00000;

	for(i=0; i<NUM_COMMANDS; i++)
		commands[i] = (7<<22);
	
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;
    
    printf("\nINFO: Starting %s example.\r\n", "stepper");
    /* Initialize the PRU */
    prussdrv_init ();	    
    /* Open PRU Interrupt */
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret)
    {
        printf("prussdrv_open open failed\n");
        return (ret);
    }
    
    /* Get the interrupt initialized */
    prussdrv_pruintc_init(&pruss_intc_initdata);

	/* load array on PRU */
	prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0, 			 delays, 	4*NUM_DELAYS);
	prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, NUM_DELAYS*4, commands, 	4*NUM_COMMANDS);

    /* Execute example on PRU */
    printf("\tINFO: Executing example.\r\n");
    prussdrv_exec_program (PRU_NUM, "./stepper.bin");
    
    /* Wait until PRU0 has finished execution */
    printf("\tINFO: Waiting for HALT command.\r\n");
    prussdrv_pru_wait_event (PRU_EVTOUT_0);
    printf("\tINFO: PRU completed transfer.\r\n");
    prussdrv_pru_clear_event (PRU0_ARM_INTERRUPT);

    /* Disable PRU and close memory mapping*/
    prussdrv_pru_disable (PRU_NUM);
    prussdrv_exit ();

    return(0);
}
