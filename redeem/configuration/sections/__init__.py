def _clean(key):
    return key.replace('-','_').lower()


class BaseConfig(object):
    """Superclass of all config 'sections'"""

    def has(self, key):
        return hasattr(self, _clean(key))

    def get(self, key):
        if not hasattr(self, _clean(key)):
            print("*****{}".format(key))
            return None
        return getattr(self, _clean(key))

    def getfloat(self, key):
        val = self.get(_clean(key))
        try:
            val = float(val)
        except ValueError:
            return None
        return val

    def getint(self, key):
        val = self.get(_clean(key))
        try:
            val = int(val)
        except ValueError:
            return None
        return val
