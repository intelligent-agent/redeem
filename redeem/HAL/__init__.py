import platform
import os, sys, inspect

# Use this if you want to include modules from a subfolder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.realpath(os.path.dirname(inspect.getfile(inspect.currentframe()))),
            'OperatingSystems', platform.system()
        )
    )
)
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)
