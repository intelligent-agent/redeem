#MakeTempTable2.py


# The formula is from Wikipedia

import math 

temp_low = 0
temp_high = 260

Tk   = 273.15
T0	 = 25 + Tk 		# Temperature 
B	 = 4267			# Beta value 
R0 	 = 10000		# Resistance at room temperature

print 'temp_chart["B57561G0103F000"] = ['

for T in range(temp_low, temp_high+1):
	R = R0*math.exp(B*((1/(T+Tk))-(1/T0)))
	print "[{}, {}],".format(T, R)
print ']'
