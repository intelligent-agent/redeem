from redeem.configuration import ConfiguredSettings


class MacOSX(object):
  def __init__(self, release_version):
    v = release_version.split('_')
    print("Running on MacOSX {}.{}".format(v[0], v[1]))
   # Capture the command line information
    ConfiguredSettings().put('Software', 'kernel', 'Darwin_{}_{}'.format(v[0], v[1]))


class Darwin_18_2(MacOSX):
  def __init__(self, path):
    release_version = "18_2"
    super().__init__(release_version)

class Darwin_18_5(MacOSX):
  def __init__(self, path):
    release_version = "18_5"
    super().__init__(release_version)
