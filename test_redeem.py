from redeem.GCodeProcessor import GCodeProcessor
from redeem.Redeem import Redeem
from redeem.Gcode import Gcode

import logging

def test_redeem():
    r = Redeem("/usr/src/redeem/configs")
    g = r.printer.processor
    for gcode in g.get_test_gcodes():
        logging.info("Testing '"+gcode.message+"'")
        g.execute(gcode)
    r.exit()
    pass

def test2():
    r = Redeem("/usr/src/redeem/configs")
    g = r.printer.processor
    g.execute( Gcode({"message": "G28", "prot": "testing"}) )
    r.exit()
    
def test3():
    from redeem.Redeem import main
    main("/usr/src/redeem/configs")
    
def test4():
    test_str = """
        G28
        G1 F5000.000
        G1 Z0.350
        G1 X-100.0 Y-100.0
        G1 X100.0 Y-100.0
        G1 X100.0 Y100.0
        G1 X-100.0 Y100.0
        G1 X0.0 Y0.0
        """
    r = Redeem("/usr/src/redeem/configs")
    g = r.printer.processor
    for line in test_str.splitlines():
        if line:
            print line
            g.execute( Gcode({"message": line, "prot":"testing"}) )
        
    r.exit()


def test_load():
    r = Redeem("/usr/src/redeem/configs")
    r.exit()

def test_run():
	from redeem.Redeem import main
    main("/usr/src/redeem/configs")

if __name__ == "__main__":
    test_load()
    print "Test finished"
