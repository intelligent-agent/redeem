#include <Python.h>
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define NUM_TOGGLES 10
#define AM33XX
 
static PyObject *pypruss_init(PyObject *self, PyObject *args)
{
    int pru_num;
    int ret;

    if (!PyArg_ParseTuple(args, "i", &pru_num)){
     	return NULL;
    }
	
	// Make sure the module is loaded
	system("modprobe uio_pruss");


    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;	
    
    prussdrv_init ();	    
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret){
        printf("prussdrv_open open failed\n");
        return NULL;
    }

    /* Get the interrupt initialized */
    prussdrv_pruintc_init(&pruss_intc_initdata);

    Py_INCREF(Py_None);
    return Py_None;
}
 
static PyObject *pypruss_set_toggles(PyObject *self, PyObject *args){
	int pru_num;
    int i;    

    unsigned int all[(NUM_TOGGLES*2)+3]; // all[0] = abort, all[N-1] = last command

    if (!PyArg_ParseTuple(args, "i", &pru_num)){
     	return NULL;
    }

	all[0] = 1; // Do not abort
    for(i=0; i<NUM_TOGGLES; i++){
		if(i%2 == 0)
            all[i+1] = (1<<12);
		else
		    all[i+1] = 0;
		all[i+NUM_TOGGLES+1] = 0x01;	
    }
    
    all[(NUM_TOGGLES*2)+2] = 0; // Last command, abort

    /* load array on PRU */
    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0,  all, ((NUM_TOGGLES*2)+3)*4);// Load commands 

    /* Execute example on PRU */
    //printf("\tINFO: Executing example.\r\n");
    prussdrv_exec_program (pru_num, "./stepper.bin");
    
    /* Wait until PRU0 has finished execution */
    //printf("\tINFO: Waiting for HALT command.\r\n");
    prussdrv_pru_wait_event (PRU_EVTOUT_0);
    //printf("\tINFO: PRU completed transfer.\r\n");
    prussdrv_pru_clear_event (PRU0_ARM_INTERRUPT);

	return Py_BuildValue("i", 0);	
}

static PyObject *pypruss_disable(PyObject *self, PyObject *args){
	int pru_num;

    if (!PyArg_ParseTuple(args, "i", &pru_num)){
     	return NULL;
    }
	
    /* Disable PRU and close memory mapping*/
    prussdrv_pru_disable(pru_num);
    prussdrv_exit();

    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef pypruss_methods[] = {
        { "init", (PyCFunction)pypruss_init, METH_VARARGS, NULL },
		{ "set_toggles", (PyCFunction)pypruss_set_toggles, METH_VARARGS, NULL},
		{ "disable", (PyCFunction)pypruss_disable, METH_VARARGS, NULL},
        { NULL, NULL, 0, NULL }
};
         
PyMODINIT_FUNC initpypruss()
{
        Py_InitModule3("pypruss", pypruss_methods, "Extenstion lib for PRUSS");
}
