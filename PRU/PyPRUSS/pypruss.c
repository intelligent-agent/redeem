#include <Python.h>
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define NUM_TOGGLES 10
#define AM33XX
#define PIN_ADDR   0x00000004
#define DELAY_ADDR (7)

static PyObject *pypruss_init(PyObject *self, PyObject *args){
    int pru_num;
    int ret;
	unsigned int halt[3] = {0};
	
    if (!PyArg_ParseTuple(args, "i", &pru_num)){					// Parse the PRU number
     	return NULL;
    }
	system("modprobe uio_pruss");									// Make sure the module is loaded
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;	
    prussdrv_init ();	    
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret){
        printf("prussdrv_open open failed\n");
        return NULL;
    }
    prussdrv_pruintc_init(&pruss_intc_initdata);					// Get the interrupt initialized
    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0,  halt, 3*4);	// Load commands 
    prussdrv_exec_program (pru_num, "./firmware.bin");				// Load and execute the program 

    Py_INCREF(Py_None);
    return Py_None;
}
 
static PyObject *pypruss_set_data(PyObject *self, PyObject *args){
	int pru_num;
    int i;    
    int len;	
	PyObject* pinObj;
	PyObject* dlyObj;
    PyObject* pinSeq;
    PyObject* dlySeq;
	PyObject* intObj;
	unsigned int *all;

    if (!PyArg_ParseTuple(args, "iOO", &pru_num, &pinObj, &dlyObj))
        return NULL;

    pinSeq = PySequence_Fast(pinObj, "expected a sequence");
    dlySeq = PySequence_Fast(dlyObj, "expected a sequence");
    len = PySequence_Size(pinObj);

	if(len != PySequence_Size(dlyObj)){ 						// Make sure the two tables are the same lengths
		return NULL;	
	}

	all = (unsigned int *)malloc(sizeof(int)*200);
	
	*(all)  = 1;
    for (i = 0; i < len; i++) {
        intObj 		= PySequence_Fast_GET_ITEM(pinSeq, i);
		*(all+1+i)  = PyInt_AsUnsignedLongMask(intObj);		
        intObj 		= PySequence_Fast_GET_ITEM(dlySeq, i);
		*(all+100+i)	= PyInt_AsUnsignedLongMask(intObj);		
    }
	//*(all+10+6+1) = 0;

    Py_DECREF(pinSeq);
    Py_DECREF(dlySeq);

    /* load array on PRU */
    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0,  all, 200*4);// Load commands

	//prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 0, 			 	abort, 	4);		// Set the abort to 0 = do not abort
    //prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, 4,   		test,   6*4);	// Load the pin data
/*    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, DELAY_ADDR, 			 delays, len*4);	// Load the delay data
    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, DELAY_ADDR+(len+1*4), end,	4);		// Set the last delay to 0
*/
	prussdrv_pru_enable ( 0 ); 	// Start the PRU

    Py_INCREF(Py_None);			// Return None to indicate Ok
    return Py_None;	
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
		{ "set_data", (PyCFunction)pypruss_set_data, METH_VARARGS, NULL},
		{ "disable", (PyCFunction)pypruss_disable, METH_VARARGS, NULL},
        { NULL, NULL, 0, NULL }
};
         
PyMODINIT_FUNC initpypruss()
{
        Py_InitModule3("pypruss", pypruss_methods, "Extenstion lib for PRUSS");
}
