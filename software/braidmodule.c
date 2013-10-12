/****
C++ version of braid_data for speeding up the process

Author: Øyvind Nydal Dahl
email: oyvdahl@online.no
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
**/


#include <Python.h>
 
PyObject* _braid_data_c(PyObject* data1, PyObject* data2)
{

    int line = 0;           //Current position in the resulting arrays
    int idx1 = 0;           //Current position in data1
    int idx2 = 0;           //Current position in data2

    //Variables for extracting tuple-values
    PyObject* tmp_tuple1;
    PyObject* tmp_tuple2;
    int pin1, pin2;
    float dly1, dly2;

    //Calculate max size (Is this correct?)
    int max_size = PyList_Size(data1) + PyList_Size(data2);
    
    // Allocate memory for two arrays of maximum possible size to contain result
    int * pins = (int*) malloc(sizeof(int) * max_size);
    float * delay = (float*) malloc(sizeof(float) * max_size);
        
    //Get first tuples from data1 and data2    
    tmp_tuple1 = PyList_GetItem(data1,idx1);
    pin1 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple1,0));
    dly1 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple1,1));
    tmp_tuple2 = PyList_GetItem(data2,idx2);
    pin2 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple2,0));
    dly2 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple2,1));
        
    while (1) {
        if (dly1 == dly2) {
            //Create resulting pin number
            pins[line] = pin1 + pin2;
            //Create resulting delay
            delay[line] = dly1;
        
            //DEBUG:
            //printf("Added (%d, %.1f) - dly1=dly2\n", pins[line], delay[line]);
            //printf("dly1=%.1f\n",dly1);
            //printf("dly2=%.1f\n",dly2);
            
            //Update line
            line++; 
            
            //Update indexes
            idx1++;
            idx2++;
            
            //Check that there are still items left in both arrays
            if (idx1 >= PyList_Size(data1) || idx2 >= PyList_Size(data2))
                break;
            
            //Get next tuples from data1 and data2
            tmp_tuple1 = PyList_GetItem(data1,idx1);
            pin1 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple1,0));
            dly1 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple1,1));
            tmp_tuple2 = PyList_GetItem(data2,idx2);
            pin2 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple2,0));
            dly2 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple2,1));
        }
        
        else if (dly1 > dly2) {
            //Create resulting pin number
            pins[line] = pin1 + pin2;
            //Create resulting delay
            delay[line] = dly2;
            
            //DEBUG:
            //printf("Added (%d, %.1f) - dly1>dly2\n", pins[line], delay[line]);
            //printf("dly1=%.1f\n",dly1);
            //printf("dly2=%.1f\n",dly2);
            //printf("idx1=%d\n",idx1);
            //printf("idx2=%d\n",idx2);
            
            //Update line
            line++; 
            
            //Subtract dly2 from dly1 to get the delay from the last tuple we added
            dly1 -= dly2;
            
            //Increase idx2
            idx2++;
            
            //Check that there are still items left in data2 array
            if (idx2 >= PyList_Size(data2))
                break;
            
            //Get next tuple from data2
            tmp_tuple2 = PyList_GetItem(data2,idx2);
            pin2 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple2,0));
            dly2 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple2,1));
        }
        
        else if (dly1 < dly2) {
            //Create resulting pin number
            pins[line] = pin1 + pin2;
            //Create resulting delay
            delay[line] = dly1;
            
            //DEBUG:
            //printf("Added (%d, %.1f) - dly1<dly2\n", pins[line], delay[line]);
            //printf("dly1=%.1f\n",dly1);
            //printf("dly2=%.1f\n",dly2);
            //printf("idx1=%d\n",idx1);
            //printf("idx2=%d\n",idx2);
            
            //Update line
            line++; 
            
            //Subtract dly1 from dly2 to get the delay from the last tuple we added
            dly2 -= dly1;
            
            //Increase idx1
            idx1++;
            
            //Check that there are still items left in data1 array
            if (idx1 >= PyList_Size(data1))
                break;
                
            //Get next tuple from data1
            tmp_tuple1 = PyList_GetItem(data1,idx1);
            pin1 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple1,0));
            dly1 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple1,1));
        }
    }    

    //If we are here, then we have gone through at least one of the arrays.
    //Need to check if there are items left in the other array

    if (idx1 < PyList_Size(data1)) 
    {
        pins[line] = pin1;
        delay[line] = dly1;
        line++;
        idx1++;

        //Iterate through any items left in data1
        for (idx1; idx1 < PyList_Size(data1); idx1++) 
        {
            //Get tuple from data1
            tmp_tuple1 = PyList_GetItem(data1,idx1);
            pin1 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple1,0));
            dly1 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple1,1));

            //Add new tuple to result
            pins[line] = pin1;
            delay[line] = dly1;
            
            //Increase indexes
            line++;
        }
    }

    if (idx2 < PyList_Size(data2)) 
    {
        pins[line] = pin2;
        delay[line] = dly2;
        line++;
        idx2++;     
            
            
        //Iterate through any items left in data2
        for (idx2; idx2 < PyList_Size(data2); idx2++) 
        {
            //Get tuple from data2
            tmp_tuple2 = PyList_GetItem(data2,idx2);
            pin2 = (int)PyInt_AsLong(PyTuple_GetItem(tmp_tuple2,0));
            dly2 = (float)PyFloat_AsDouble(PyTuple_GetItem(tmp_tuple2,1));

            //Add new tuple to result
            pins[line] = pin2;
            delay[line] = dly2;
            
            //Increase indexes
            line++;
        }
    }


    //Print result for debugging:
    //printf("\nResulting array:\n");
    //for (int i=0; i<line; i++)
    //    printf("(%d, %.1f), ", pins[i], delay[i]);

    //printf("\n\n");    


    //Create a returnable object from the two arrays "pins" and "delay"
    PyObject *pylist = PyList_New(line);
    int i;
    for (i=0; i<line; i++){
		PyList_SetItem(pylist, i, Py_BuildValue("(id)", pins[i], delay[i]));
    }

    //Free allocated memory
    free(pins);
    free(delay);
	
    //Return array
    return pylist;
}



static PyObject* braid_data_c(PyObject* self, PyObject* args)
{
    PyObject *data1;
    PyObject *data2;
    
    //Extract the two arrays of data from argument object
    if (!PyArg_ParseTuple(args, "OO", &data1, &data2))
        return NULL;
    
    return Py_BuildValue("N", _braid_data_c(data1, data2));
}



static PyMethodDef BraidMethods[] =
{
     {"braid_data_c", braid_data_c, METH_VARARGS, "Combine data from two sources into one"},
     {NULL, NULL, 0, NULL}
};
 
PyMODINIT_FUNC
 
initbraid(void)
{
     (void) Py_InitModule("braid", BraidMethods);
}
