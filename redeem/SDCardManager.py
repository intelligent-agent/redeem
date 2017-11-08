from multiprocessing import Lock


class SDCardManager(object):
    current_file = None
    current_byte_count = None
    current_file_size = None
    current_lock = None

    def __init__(self):
        self.current_lock = Lock()
