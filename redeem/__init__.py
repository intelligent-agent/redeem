# -*- coding: utf-8 -*-
from __future__ import absolute_import
__url__ = "https://github.com/intelligent-agent/redeem"

from ._version import get_versions
__long_version__ = get_versions()['version']

try:
  __base_version__, __split_version__ = __long_version__.split('+')
  __ext__, __branch__, __uuid__ = __split_version__.split('.')[:3]
  if __branch__ in set(['dev', 'a', 'b', 'RC']):
    __version__ = "{}{}{}".format(__base_version__, __branch__, __ext__)
  elif __base_version__.split('.')[:2] == __branch__.split('_')[:2]:
    __version__ = "{}-{}".format(__base_version__, __ext__)
  else:
    __version__ = "{}-{}+{}".format(__branch__, __base_version__, __ext__)
  del __base_version__
  del __split_version__
  del __ext__
  del __uuid__
except ValueError:
  __version__ = __long_version__
  __branch__ = ''

del get_versions
