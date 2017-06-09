#!/usr/bin/python

from redeem.GCodeProcessor import GCodeProcessor
from redeem.Redeem import Redeem
from redeem.Gcode import Gcode

import logging

def test_redeem():
    r = Redeem("/usr/src/redeem/configs")
    r.printer.enable.set_enabled()
    g = r.printer.processor
    for gcode in g.get_test_gcodes():
        logging.info("Testing '"+gcode.message+"'")
        g.execute(gcode)
    r.exit()
    pass


def test_load():
    r = Redeem("/usr/src/redeem/configs")
    r.exit()

def test_run():
    from redeem.Redeem import main
    main("/usr/src/redeem/configs")
    
def test_code(test_str):
    r = Redeem("/usr/src/redeem/configs")
    r.printer.enable.set_enabled()
    g = r.printer.processor
    for line in test_str.splitlines():
        if line:
            print line
            g.execute( Gcode({"message": line, "prot":"testing"}) )
        
    r.exit()
    
def test_file(test):
    r = Redeem("/usr/src/redeem/configs")
    r.printer.enable.set_enabled()
    g = r.printer.processor
    f = open(test,'r')
    for line in f.readlines():
        if line:
            print line
            g.execute( Gcode({"message": line, "prot":"testing"}) )
    
    r.exit()
    f.close()

if __name__ == "__main__":

    test_str = """
    G28 Z0
    """    
    
    test_code(test_str)
    
    print "Test finished"
