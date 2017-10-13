class BaseConfig(object):
    """Superclass of all config 'sections'"""

    def get(self, key):
        if not getattr(self, key, None):
            return None
        return getattr(self, key)

    def getfloat(self, key):
        val = self.get(key)
        try:
            val = float(val)
        except ValueError:
            return None
        return val

    def getint(self, key):
        val = self.get(key)
        try:
            val = int(val)
        except ValueError:
            return None
        return val
