from multiprocessing import Lock
import os


def blocks(files, size=65536):
  while True:
    b = files.read(size)
    if not b:
      break
    yield b


class SDCardManager(object):
  file_name = None
  gcode_file = None
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
    open the file, remains open until another file is opened
    """
    self.lock.acquire()

    self.file_name = f

    if self.gcode_file:
      self.gcode_file.close()

    self.gcode_file = open(self.file_name, 'r')

    self.line_count = 0
    self.byte_count = 0

    # file size in bytes
    self.file_byte_size = os.path.getsize(self.file_name)

    # file size in lines
    self.file_line_size = sum(bl.count("\n") for bl in blocks(self.gcode_file))
    self.gcode_file.seek(-1, 2)
    end = self.gcode_file.read()
    if end != "\n":
      self.file_line_size += 1

    #reset file position
    self.gcode_file.seek(0)

    self.lock.release()
    return True

  def next(self):
    """
    return the next line in the file and increment counters
    """
    self.lock.acquire()
    lc = self.line_count
    N = self.file_line_size
    active = self.active
    self.lock.release()

    if not active:
      raise StopIteration()
      return

    if (lc < N):
      self.lock.acquire()
      line = self.gcode_file.readline()
      self.byte_count += len(line.encode('utf-8'))
      self.line_count += 1
      self.lock.release()
      return line
    else:
      self.lock.acquire()
      self.byte_count = self.file_byte_size
      self.line_count = N
      self.lock.release()
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
    return the current position within the file,
    both line count and number of bytes
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

  def set_status(self, status):
    """
    set the status of the current file
    """
    self.lock.acquire()
    self.active = bool(status)
    self.lock.release()

  def set_position(self, byte_position=0, line_position=0):
    """
    set the counters that define our current position within the file

    inputs may be either line index or some amount of bytes,
    bytes will be converted to a line position
    """
    self.lock.acquire()

    # reset file object
    self.gcode_file.seek(0)

    # walk through the file line by line until we find a location that
    # matches either line position or byte count
    if (byte_position > 0) or (line_position > 0):

      i = 0
      b = 0
      for line in self.gcode_file:
        ls = len(line.encode('utf-8'))
        if (byte_position > 0) and (byte_position < b + ls):
          break
        elif (line_position > 0) and (line_position == i):
          break

        i += 1
        b += ls

      line_position = i
      byte_position = b

    self.line_count = line_position
    self.byte_count = byte_position
    self.lock.release()

    return line_position, byte_position

  def reset(self):
    """
    reset all values to default
    """
    self.file_name = None
    self.byte_count = None
    self.line_count = None
    self.file_byte_size = None
    self.file_line_size = None
