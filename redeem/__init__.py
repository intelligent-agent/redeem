# coding: utf-8
__url__ = "https://github.com/intelligent-agent/redeem"

from ._version import get_versions
__long_version__ = get_versions()['version']
__version__ = __long_version__.split('+')[0]
del get_versions
