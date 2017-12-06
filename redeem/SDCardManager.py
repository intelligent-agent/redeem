from multiprocessing import Lock


class SDCardManager(object):
    file_name = None
    lines = []
    lines_size = []
    byte_count = None
    line_count = None
    file_byte_size = None
    file_line_size = None
    active = False
    lock = None

    def __init__(self):
        self.lock = Lock()
        
    def __iter__(self):
        return self

    def load_file(self, f):
        """
        read the file in as a list of lines
        """
            
        with open(f, 'r') as gcode_file:

            self.lock.acquire()
            self.file_name = f
            self.line_count = 0
            self.byte_count = 0
            self.file_byte_size = 0
            self.file_line_size = 0
            self.lines = []
            self.lines_size = []
            self.lock.release()

            gcode_file.seek(0)

            for line in gcode_file:
                self.lock.acquire()
                self.file_line_size += 1
                self.file_byte_size += len(line.encode('utf-8'))
                self.lines.append(line)
                self.lines_size.append(self.file_byte_size) # cumulative sum of bytes
                self.lock.release()
            
            return True
            
    def next(self):
        """
        return the next line in the list and increment counters
        """
        
        self.lock.acquire()
        lc = self.line_count
        N = self.file_line_size
        status = self.active
        self.lock.release()
        
        if (lc < N) and status:
            self.lock.acquire()
            out = self.lines[self.line_count]
            self.byte_count = self.lines_size[self.line_count]
            self.line_count += 1
            self.lock.release()
            return out
        else:
            raise StopIteration()
            
    def get_file_size(self):
        """
        return the size of the file
        """
        
        self.lock.acquire()
        szb = self.file_byte_size
        szl = self.file_line_size
        self.lock.release()
        
        return szl, szb
        
    def get_file_name(self):
        """
        return the name of the file
        """
        
        self.lock.acquire()
        fn = self.file_name
        self.lock.release()
        
        return fn
        
    def get_position(self):
        """
        return the current position within the file, both line count 
        and number of bytes
        """
        
        self.lock.acquire()
        line_position = self.line_count
        byte_position = self.byte_count
        self.lock.release()
        
        return line_position, byte_position
        
    def get_status(self):
        """
        get the status of the current file
        """
        
        self.lock.acquire()
        st = self.active
        self.lock.release()
        
        return st
        
    def set_active(self, status):
        """
        get the status of the current file
        """
        
        self.lock.acquire()
        self.active = bool(status)
        self.lock.release()
        
        return
        
    
    def set_position(self, byte_position=0, line_position=0):
        """
        set the counters that define our current position within the file
        
        inputs may be either line index or some amount of bytes, bytes 
        will be converted to a line position
        """
        
        if byte_position > 0:
            self.lock.acquire()
            szs = self.lines_size
            self.lock.release()
            for i, b in enumerate(szs):
                if byte_position < b:
                    line_position = i
                    byte_position = b
                    break
        
        self.lock.acquire()
        self.line_count = line_position
        self.byte_count = byte_position
        self.lock.release()
        
        return line_position, byte_position
        
        
    def reset(self):
        """
        reset all values to default
        """
        
        self.file_name = None
        self.lines = []
        self.lines_size = []
        self.byte_count = None
        self.line_count = None
        self.file_byte_size = None
        self.file_line_size = None
        
