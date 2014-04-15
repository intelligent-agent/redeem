'''
G-code interpreter for Replicape. 
For more info see:
http://reprap.org/wiki/G-code

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import logging

# A command received from pronterface or whatever
class Gcode:

    line_number = 0
    ''' Init; parse the token '''
    def __init__(self, packet):
        try:
            self.message = packet["message"].split(";")[0]
            self.message = self.message.strip(' \t\n\r')
            self.prot = packet["prot"] if "prot" in packet else "None"
            self.has_crc = False
            self.answer = "ok"
            #print packet
            if len(self.message) == 0:
                #print packet
                logging.debug("Empty message")
                self.gcode = "No-Gcode"
                return 
            self.tokens = self.message.split(" ")
            if self.tokens[0][0] == "N":                                # Ok, checksum
                line_num = self.message.split(" ")[0][1::]
                cmd = self.message.split("*")[0]                             # Command
                csc = self.message.split("*")[1]                             # Command to compare with
                if int(csc) != self._getCS(cmd):
                    logging.error("CRC error!")
                self.message =  self.message.split("*")[0][(1+len(line_num)+1)::] # Remove crc stuff
                self.line_number = int(line_num)                        # Set the line number
                Gcode.line_number += 1                                  # Increase the global counter 
                self.has_crc = True
            
            # Parse 
            self.tokens = self.message.split(" ")    
            self.gcode = self.tokens.pop(0) # gcode number
            self.tokens = filter(None, self.tokens)        
        except Exception as e:
            logging.exception("Ooops: ")

    ''' Return True if the command has to be processed immediatly '''
    def is_urgent(self):
        return False

    ''' The machinecode '''
    def code(self):
        return self.gcode

    ''' Get the letter '''
    def token_letter(self, index):
        return self.tokens[index][0]

    ''' Get the value aafter the letter '''
    def token_value(self, index):
        return self.tokens[index][1::]
     
    ''' Return the tokens '''
    def get_tokens(self):
        return self.tokens   

    ''' Set the tokens '''
    def set_tokens(self, tokens):
        self.tokens = tokens

    ''' Check if the letter exists as token '''
    def has_letter(self, letter):
        for token in self.tokens:
            if token[0] == letter:
                return True
        return False
    
    def get_value_by_letter(self, letter):
        for token in self.tokens:           
            if token[0] == letter:
                return token[1::]
        return None

    ''' Get an int or return a default value '''    
    def get_int_by_letter(self, letter, default):
        if self.has_letter(letter):
            return int(self.get_value_by_letter(letter))
        return int(default)

    def remove_token_by_letter(self, letter):
         for i, token in enumerate(self.tokens):
            if token[0] == letter:
                self.tokens.pop(i)

    def num_tokens(self):
        return len(self.tokens)

    ''' Compute a Checksum of the letters in the command '''
    def _getCS(self, cmd):
        cs = 0
        for c in cmd:            
            cs = cs ^ ord(c)
        return cs

    def is_crc(self):
        ''' Return True if this segment was a numbered line '''
        return self.has_crc

    ''' Get the result of the execution '''
    def get_answer(self):
        return self.answer
    
    ''' Set a new answer other than 'ok'  '''
    def set_answer(self, answer):
        self.answer = answer






