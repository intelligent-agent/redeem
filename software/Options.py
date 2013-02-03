'''
Options for the Replicape. 
For more info see:
http://reprap.org/wiki/G-code

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''
class Options: 
	''' Init '''
	def __init__(self):
		self.options = {}

	''' Get a value by key '''
	def get(key):
		if key in self.options:
			return self.options[key]
		return None

	''' set a value by key '''
	def set(key, value):
		self.options[key]  = value

