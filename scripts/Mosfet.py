import bbio as io


class Mosfet:

	def __init__(self, pin):
		self.pin = pin
		io.pwmEnable(pin) # Init the Pin to PWM mode
		io.pwmFrequency(pin, 20000) # Set a frequency, not important for now

	'''Set duty cycle between 0 and 1'''
	def setPower(self, value):
		io.analogWrite(self.pin, int(value*255.0))

	'''Set the PWM frequency'''
	def setFrequency(self, freq):
		io.pwmFrequency(self.pin, freq)

