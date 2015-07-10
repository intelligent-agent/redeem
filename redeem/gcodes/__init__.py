import os
import glob

#Import all python files as submodule
for f in glob.glob(os.path.dirname(__file__) + "/*.py"):
    if os.path.isfile(f) and not f.endswith('__init__.py') and \
            not f.endswith('GCodeCommand.py'):
        moduleName = os.path.splitext(os.path.basename(f))[0]
        __import__(moduleName, locals(), globals())
