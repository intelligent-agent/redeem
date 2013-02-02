/*
PyPRUSS - a Python binding for the PRU driver on BeagleBone 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
*/

#include <Python.h>
#include <prussdrv.h>
#include <pruss_intc_mapping.h>

#define AM33XX

#define PRU_NUM0 0
#define PRU_NUM1 1

static void *pruDataMem;
static unsigned int *pruDataMem_int;

static int mem_fd;
static void *ddrMem, *sharedMem;
static unsigned int *sharedMem_int;

// Higher level function 
static PyObject *pypruss_init_all(PyObject *slef, PyObject *args){
    int ret;
	unsigned int data[1];
	tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;
    prussdrv_init ();	
	ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret){
        printf("prussdrv_0_open open failed\n");
        return NULL;
    }
    
    ret = prussdrv_open(PRU_EVTOUT_1);
    if (ret){
        printf("prussdrv_1_open open failed\n");
        return NULL;
    }
    prussdrv_pruintc_init(&pruss_intc_initdata);

	data[0] = 0;
	prussdrv_pru_write_memory(0, 0,  data, 4);
	prussdrv_pru_write_memory(1, 0,  data, 4);
    prussdrv_exec_program (PRU_NUM0, "./firmware_PRU0.bin");
    prussdrv_exec_program (PRU_NUM1, "./firmware_PRU1.bin");

    Py_INCREF(Py_None);
    return Py_None;

}

// Wait for all PRUs to return 
static PyObject *pypruss_wait_for_both(PyObject *self, PyObject *args){
    prussdrv_pru_wait_event (PRU_EVTOUT_0);
    prussdrv_pru_clear_event (PRU0_ARM_INTERRUPT);
    prussdrv_pru_wait_event (PRU_EVTOUT_1);
    prussdrv_pru_clear_event (PRU1_ARM_INTERRUPT);

    Py_INCREF(Py_None);
    return Py_None;	
}


// Modprobe 
static PyObject *pypruss_modprobe(PyObject *self, PyObject *args){
	system("modprobe uio_pruss");									
    Py_INCREF(Py_None);
    return Py_None;
}


// Init
static PyObject *pypruss_init(PyObject *self, PyObject *args){
    prussdrv_init ();	    
    Py_INCREF(Py_None);
    return Py_None;
}

// Open 
static PyObject *pypruss_open(PyObject *self, PyObject *args){
    int ret;
	int evtout;

	if (!PyArg_ParseTuple(args, "i", &evtout)){
     	return NULL;
    }
    ret = prussdrv_open(evtout);
    if (ret){
        printf("prussdrv_open open failed\n");
        return NULL;
    }
    Py_INCREF(Py_None);
    return Py_None;
}

// Reset a PRU
static PyObject *pypruss_pru_reset(PyObject *self, PyObject *args){
	int pru_num;
	if (!PyArg_ParseTuple(args, "i", &pru_num))
        return NULL;
	prussdrv_pru_reset(pru_num); 										// Enable the PRU
    Py_INCREF(Py_None);						
    return Py_None;	
}

// Disable a PRU
static PyObject *pypruss_pru_disable(PyObject *self, PyObject *args){
	int pru_num;
	if (!PyArg_ParseTuple(args, "i", &pru_num))
        return NULL;
	prussdrv_pru_disable(pru_num); 										// Enable the PRU
    Py_INCREF(Py_None);						
    return Py_None;	
}

// Enable a PRU
static PyObject *pypruss_pru_enable(PyObject *self, PyObject *args){
	int pru_num;
	if (!PyArg_ParseTuple(args, "i", &pru_num))
        return NULL;
	prussdrv_pru_enable(pru_num); 											// Start the PRU
    Py_INCREF(Py_None);													// Return None to indicate Ok
    return Py_None;	
}

// Write data to the memory
static PyObject *pypruss_pru_write_memory(PyObject *self, PyObject *args){
	int mem_type;		// PRUSS0_PRU0_DATARAM or PRUSS0_PRU1_DATARAM
    int i;    
    int len;	
	int offset;
	PyObject* data_obj;
	PyObject* int_obj;
	PyObject* data_seq;
	unsigned int *data;

    if (!PyArg_ParseTuple(args, "iiO", &mem_type, &offset, &data_obj))
        return NULL;

    data_seq = PySequence_Fast(data_obj, "expected a sequence");
    len = PySequence_Size(data_obj);
	data = (unsigned int *)calloc(len, 4);

    for (i = 0; i < len; i++) {
        int_obj	= PySequence_Fast_GET_ITEM(data_seq, i);
		data[i] = PyInt_AsUnsignedLongMask(int_obj);		
    }
    Py_DECREF(data_seq);


    prussdrv_pru_write_memory(mem_type, offset,  data, len*4);

    Py_INCREF(Py_None);													
    return Py_None;	
}

// Interrupt init
static PyObject *pypruss_pruintc_init(PyObject *self, PyObject *args){
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;	
    prussdrv_pruintc_init(&pruss_intc_initdata);					// Get the interrupt initialized

    Py_INCREF(Py_None);
    return Py_None;
}

//map_l3mem
static PyObject *pypruss_map_l3mem(PyObject *self, PyObject *args){
	unsigned int *l3mem;
    prussdrv_map_l3mem(&l3mem); 

    printf("Not implemented\n");
	return NULL;

    Py_INCREF(Py_None);													
    return Py_None;	
}

//map_extmem
static PyObject *pypruss_map_extmem(PyObject *self, PyObject *args){
	unsigned int *extmem;
    prussdrv_map_extmem(&extmem); 

    printf("Not implemented\n");
	return NULL;

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
 

// Wait for an event from a PRU
static PyObject *pypruss_wait_for_event(PyObject *self, PyObject *args){
	int evtout; // PRU_EVTOUT_0 or PRU_EVTOUT_1
    if (!PyArg_ParseTuple(args, "i", &evtout))
     	return NULL;	
	prussdrv_pru_wait_event (evtout);			// Wait for the event. This blocks the thread. 
    Py_INCREF(Py_None);
    return Py_None;
}

// Clear an event 
static PyObject *pypruss_clear_event(PyObject *self, PyObject *args){
	int event; // PRU0_ARM_INTERRUPT or PRU1_ARM_INTERRUPT
    if (!PyArg_ParseTuple(args, "i", &event))
     	return NULL;
	prussdrv_pru_clear_event (event); 	// Clear the event 
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
		{ "init_all", (PyCFunction)pypruss_init_all, METH_VARARGS, NULL },
		{ "wait_for_both", (PyCFunction)pypruss_wait_for_both, METH_VARARGS, NULL },
        { "modprobe", (PyCFunction)pypruss_modprobe, METH_VARARGS, NULL },
        { "init", (PyCFunction)pypruss_init, METH_VARARGS, NULL },
        { "open", (PyCFunction)pypruss_open, METH_VARARGS, NULL },
		{ "pru_reset", (PyCFunction)pypruss_pru_reset, METH_VARARGS, NULL},
		{ "pru_disable", (PyCFunction)pypruss_pru_disable, METH_VARARGS, NULL},
		{ "pru_enable", (PyCFunction)pypruss_pru_enable, METH_VARARGS, NULL},		
		{ "pru_write_memory", (PyCFunction)pypruss_pru_write_memory, METH_VARARGS, NULL},
        { "pruintc_init", (PyCFunction)pypruss_pruintc_init, METH_VARARGS, NULL },
        { "map_l3mem", (PyCFunction)pypruss_map_l3mem, METH_VARARGS, NULL },
        { "map_extmem", (PyCFunction)pypruss_map_extmem, METH_VARARGS, NULL },
        { "exec_program", (PyCFunction)pypruss_exec_program, METH_VARARGS, NULL },
		{ "wait_for_event", (PyCFunction)pypruss_wait_for_event, METH_VARARGS, NULL},
		{ "clear_event", (PyCFunction)pypruss_clear_event, METH_VARARGS, NULL},		
		{ "exit", (PyCFunction)pypruss_exit, METH_VARARGS, NULL},
        { NULL, NULL, 0, NULL }
};
 
// Some sort of init stuff.         
PyMODINIT_FUNC initpypruss()
{
        Py_InitModule3("pypruss", pypruss_methods, "Extenstion lib for PRUSS");
}
