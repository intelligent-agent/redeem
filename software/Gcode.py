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

import logging

# A command received from pronterface or whatever
class Gcode:

    line_number = 0
    ''' Init; parse the token '''
    def __init__(self, packet, printer):
        self.message = packet["message"].split(";")[0]
        #logging.debug(self.message)		
        self.prot = packet["prot"]
        self.p = printer		
        self.has_crc = False

        self.tokens = self.message.split(" ")
        if self.tokens[0][0] == "N":                                # Ok, checksum
            line_num = self.message.split(" ")[0][1::]
            cmd = self.message.split("*")[0]                             # Command
            csc = self.message.split("*")[1]                             # Command to compare with
            if int(csc) != self.getCS(cmd):
                logging.error("CRC error!")
            self.message =  self.message.split("*")[0][(1+len(line_num)+1)::] # Remove crc stuff
            self.line_number = int(line_num)                        # Set the line number
            Gcode.line_number += 1                                  # Increase the global counter 
            self.has_crc = True
        
        # Parse 
        self.tokens = self.message.split(" ")    
        self.gcode = self.tokens.pop(0) # gcode number
        for i, token in enumerate(self.tokens):
            if len(token) == 0:
                self.tokens.pop(i)            
        self.debug = 0
        self.answer = "ok"

    ''' The machinecode '''
    def code(self):
        return self.gcode

    ''' Get the letter '''
    def tokenLetter(self, index):
        return self.tokens[index][0]

    ''' Get the value aafter the letter '''
    def tokenValue(self, index):
        return self.tokens[index][1::]
     
    ''' Return the tokens '''
    def tokens(self):
        return self.tokens   

    ''' Set the tokens '''
    def setTokens(self, tokens):
        self.tokens = tokens

    ''' Check if the letter exists as token '''
    def hasLetter(self, letter):
        for token in self.tokens:
            if token[0] == letter:
                return True
        return False
    
    ''' Get a token value by the token letter '''
    def getValueByLetter(self, letter):
        for token in self.tokens:           
            if token[0] == letter:
                return token[1::]
        return None

    ''' Remove a token by it's letter '''
    def removeTokenByLetter(self, letter):
         for i, token in enumerate(self.tokens):
            if token[0] == letter:
                self.tokens.pop(i)

    def numTokens(self):
        return len(self.tokens)

    ''' Get the tokens '''
    def getTokens(self):
        return self.tokens

    ''' Compute a Checksum of the letters in the command '''
    def getCS(self, cmd):
        cs = 0
        for c in cmd:            
            cs = cs ^ ord(c)
        return cs

    def is_crc(self):
        ''' Return True if this segment was a numbered line '''
        return self.has_crc

    ''' Get the result of the execution '''
    def getAnswer(self):
        return self.answer
    
    ''' Set a new answer other than 'ok'  '''
    def setAnswer(self, answer):
        self.answer = answer






