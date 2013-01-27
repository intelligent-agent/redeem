#include <Python.h>
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define AM33XX

// Init, mod_probe
static PyObject *pypruss_init(PyObject *self, PyObject *args){
    int ret;

	system("modprobe uio_pruss");									// Make sure the module is loaded

    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;	
    prussdrv_init ();	    

    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret){
        printf("prussdrv_open open failed\n");
        return NULL;
    }
    prussdrv_pruintc_init(&pruss_intc_initdata);					// Get the interrupt initialized

    Py_INCREF(Py_None);
    return Py_None;
}

// Execute a program 
static PyObject *pypruss_exec_program(PyObject *self, PyObject *args){
    int pru_num;
	char* filename;

    if (!PyArg_ParseTuple(args, "is", &pru_num, &filename)){		// Parse the PRU number
     	return NULL;
    }

    prussdrv_exec_program (pru_num, filename);						// Load and execute the program 
	
	Py_INCREF(Py_None);
    return Py_None;
}
 
// Write data to the memory
static PyObject *pypruss_write_memory(PyObject *self, PyObject *args){
	int pru_num;
    int i;    
    int len;	
	int offset;
	PyObject* data_obj;
	PyObject* int_obj;
	PyObject* data_seq;
	unsigned int *data;

    if (!PyArg_ParseTuple(args, "iiO", &pru_num, &offset, &data_obj))
        return NULL;

    data_seq = PySequence_Fast(data_obj, "expected a sequence");
    len = PySequence_Size(data_obj);
	data = (unsigned int *)calloc(len, 4);

    for (i = 0; i < len; i++) {
        int_obj	= PySequence_Fast_GET_ITEM(data_seq, i);
		data[i] = PyInt_AsUnsignedLongMask(int_obj);		
    }
    Py_DECREF(data_seq);

	if(pru_num == 0)
	    prussdrv_pru_write_memory(PRUSS0_PRU0_DATARAM, offset,  data, len*4);
	else
	    prussdrv_pru_write_memory(PRUSS0_PRU1_DATARAM, offset,  data, len*4);

    Py_INCREF(Py_None);													
    return Py_None;	
}

// Enable a PRU
static PyObject *pypruss_enable(PyObject *self, PyObject *args){
	int pru_num;
	
	if (!PyArg_ParseTuple(args, "i", &pru_num))
        return NULL;
	prussdrv_pru_enable(pru_num); 											// Start the PRU
    Py_INCREF(Py_None);													// Return None to indicate Ok
    return Py_None;	
}

// Disable a PRU
static PyObject *pypruss_disable(PyObject *self, PyObject *args){
	int pru_num;
	if (!PyArg_ParseTuple(args, "i", &pru_num))
        return NULL;
	prussdrv_pru_disable(pru_num); 										// Enable the PRU
    Py_INCREF(Py_None);						
    return Py_None;	
}


// Wait for the "finished" event from the PRU and clear it. 
static PyObject *pypruss_wait_for_event(PyObject *self, PyObject *args){
	int pru_num;

    if (!PyArg_ParseTuple(args, "i", &pru_num)){
     	return NULL;
    }
	
	prussdrv_pru_wait_event (PRU_EVTOUT_0);			// Wait for the event. This blocks the thread. 
	prussdrv_pru_clear_event (PRU0_ARM_INTERRUPT); 	// Clear the event 

    Py_INCREF(Py_None);
    return Py_None;
}

// Exit the PRU driver
static PyObject *pypruss_exit(PyObject *self, PyObject *args){	
    prussdrv_exit();
    Py_INCREF(Py_None);
    return Py_None;
}

// Declare the methods to export
static PyMethodDef pypruss_methods[] = {
        { "init", (PyCFunction)pypruss_init, METH_VARARGS, NULL },
        { "exec_program", (PyCFunction)pypruss_exec_program, METH_VARARGS, NULL },
		{ "write_memory", (PyCFunction)pypruss_write_memory, METH_VARARGS, NULL},
		{ "wait_for_event", (PyCFunction)pypruss_wait_for_event, METH_VARARGS, NULL},
		{ "enable", (PyCFunction)pypruss_enable, METH_VARARGS, NULL},
		{ "disable", (PyCFunction)pypruss_disable, METH_VARARGS, NULL},
		{ "exit", (PyCFunction)pypruss_exit, METH_VARARGS, NULL},
        { NULL, NULL, 0, NULL }
};
 
// Some sort of init stuff.         
PyMODINIT_FUNC initpypruss()
{
        Py_InitModule3("pypruss", pypruss_methods, "Extenstion lib for PRUSS");
}
