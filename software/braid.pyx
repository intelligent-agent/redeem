import numpy as np

''' braid data natively '''
def _braid_data(data1, data2):
    """ Braid/merge together the data from the two data sets"""
    line = 0
    (pin1, dly1) = data1[line]
    (pin2, dly2) = data2.pop(0)
    while True: 
        dly = min(dly1, dly2)
        dly1 -= dly    
        dly2 -= dly
        try:
            if dly1 == 0 and dly2 == 0:
                data1[line] = (pin1+pin2, dly)
                (pin1, dly1) = data1[line+1]
                (pin2, dly2) = data2.pop(0)
            elif dly1 == 0:
                data1[line] = (pin1+pin2, dly)
                (pin1, dly1) = data1[line+1]
            elif dly2 == 0:    
                data1.insert(line, (pin1+pin2, dly))
                (pin2, dly2) = data2.pop(0)
            line += 1
        except IndexError, e:
            break

 
        if dly2 > 0:   
            data1[line] =  (data1[line][0], data1[line][1]+dly2)        
        elif dly1 > 0:
            data1[line] = (data1[line][0], data1[line][1]+dly1)  
            data1.pop(line+1)
         
        while len(data2) > 0:
            line += 1
            (pin2, dly2) = data2.pop(0)
            data1.append((pin2+pin1, dly2))
        while len(data1) > line+1:
            line += 1
            (pin1, dly1) = data1[line]
            data1[line] = (pin2+pin1, dly1)

    return data1

