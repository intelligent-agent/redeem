

'''
http://reprap.org/wiki/G-code
'''

# A command received from pronterface or whatever
class Gcode:
	def __init__(self, message, printer):
		self.p = printer		
		# Parse 
		self.tokens = message.split(" ")
		self.type = self.tokens[0][0] # M or G
		self.code = int(self.tokens[0][1::]) # gcode number
		print "Type: '"+self.type+"'"
		print "Code: '"+str(self.code)+"'"
		self.answer = None

	# Execute and return the answer
	def execute(self):
		if self.type == "M":
			if self.code == 104: # Extruder temperature
				self.p.ext1.setTargetTemperature(int(self.tokens[1][1::]))
			if self.code == 105: # Get Temperature
				self.answer = "T:"+str(self.p.ext1.getTemperature())+" B:"+str(self.p.hbp.getTemperature())							
			if self.code == 140: # Bed temperature
				self.p.hbp .setTargetTemperature(int(self.tokens[1][1::]))
			
	# Is there an answer?
	def hasAnswer(self):
		return True if self.answer != None else False

	# Get the result of the execution
	def getAnswer(self):
		return self.answer
