
import glob
import shutil
import logging
import os

# Charts for different thermistors.

# Copy/create data files if not present
if not os.path.exists("/etc/redeem/SEMITEC-104GT-2.cht"):
    if not os.path.isdir("/etc/redeem"):
        os.makedirs("/etc/redeem/")
    dirname = os.path.dirname(os.path.realpath(__file__))
    logging.warning("/etc/redeem/SEMITEC-104GT-2.cht does not exist, copying it...")
    for f in glob.glob(dirname+"/data/*.cht"):
        logging.warning(f)
        shutil.copy(f, "/etc/redeem")

# define a dictionary for temperature charts
temp_chart = {}

# load all temperature charts
for f in glob.glob("/etc/redeem/*.cht"):
    execfile(f)