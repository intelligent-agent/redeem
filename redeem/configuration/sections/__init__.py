from redeem.configuration.utils import clean_key as _
from redeem.configuration.exceptions import InvalidConfigOptionException


class BaseConfig(object):
    """Superclass of all config 'sections'"""

    def has(self, key):
        return hasattr(self, _(key))

    def get(self, key):
        if not hasattr(self, _(key)):
            return None
        return getattr(self, _(key))

    def set(self, key, val):
        if not hasattr(self, _(key)):
            raise InvalidConfigOptionException()
        setattr(self, _(key), val)

    def getfloat(self, key):
        val = self.get(_(key))
        try:
            val = float(val)
        except ValueError:
            return None
        return val

    def getint(self, key):
        val = self.get(_(key))
        try:
            val = int(val)
        except ValueError:
            return None
        return val

    def getboolean(self, key):
        val = self.get(_(key))
        return val in ['True', 'true', True]

