
import glob
import logging

# Charts for different thermistors.
temp_chart = {}

# get a list 
files = glob.glob("/etc/redeem/*.cht")

if not files:
    logging.warning("no temperature charts found in /etc/redeem/")
else:
    # load all temperature charts
    for f in files:
        execfile(f)