'''
G-code interpreter for Replicape. 
For more info see:
http://reprap.org/wiki/G-code

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

# A command received from pronterface or whatever
class Gcode:
	def __init__(self, message, printer):
		self.p = printer		
		# Parse 
		self.tokens = message.split(" ")
		self.type = self.tokens[0][0] # M or G
		self.code = int(self.tokens[0][1::]) # gcode number
		self.debug = 0
		self.answer = None

		if self.debug > 1:
			print "Type: '"+self.type+"'"
			print "Code: '"+str(self.code)+"'"

	# Execute and return the answer
	def execute(self):
		if self.type == "G": 
			if self.code == 1: # Move (G1 X0.1 F3000)
				axis = self.tokens[1][0] 
				print "Axis is '"+axis+"'"
				mm = float(self.tokens[1][1::])
				feed_rate = int(self.tokens[2][1::])
				self.p.move(axis, mm, feed_rate)
			if self.code == 90: # Absolute positioning
				self.p.setPositionAbsolute()
			if self.code == 91: # Relative positioning 
				self.p.setPositionRelative()				
		if self.type == "M":
			if self.code == 84: 
				self.p.disableAllSteppers()
			if self.code == 104: # Extruder temperature
				self.p.ext1.setTargetTemperature(float(self.tokens[1][1::]))
			if self.code == 105: # Get Temperature
				self.answer = "T:"+str(int(self.p.ext1.getTemperature()))+" B:"+str(int(self.p.hbp.getTemperature()))
			if self.code == 140: # Bed temperature
				self.p.hbp .setTargetTemperature(float(self.tokens[1][1::]))
			
	# Is there an answer?
	def hasAnswer(self):
		return True if self.answer != None else False

	# Get the result of the execution
	def getAnswer(self):
		return self.answer
