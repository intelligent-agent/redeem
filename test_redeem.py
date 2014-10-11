from redeem.GCodeProcessor import GCodeProcessor
from redeem.Redeem import Redeem

import logging

def test_redeem():
    r = Redeem()
    g = r.printer.processor
    for gcode in g.get_test_gcodes():
        g.execute(gcode)
    r.exit()
    pass

if __name__ == "__main__":
    test_redeem()

