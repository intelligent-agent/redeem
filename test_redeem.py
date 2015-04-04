from redeem.GCodeProcessor import GCodeProcessor
from redeem.Redeem import Redeem

import logging

def test_redeem():
    r = Redeem()
    g = r.printer.processor
    for gcode in g.get_test_gcodes():
        logging.info("Testing '"+gcode.message+"'")
        g.execute(gcode)
    r.exit()
    pass

def test2():
    r = Redeem()
    g = r.printer.processor
    g.execute( Gcode({"message": "G28", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X-100 Y-100", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X100 Y-100", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X100 Y100", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X-100 Y100", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X-100 Y-100", "prot": "Test"}) )
    g.execute( Gcode({"message": "G0 X0 Y0", "prot": "Test"}) )
    g.execute( Gcode({"message": "G28", "prot": "Test"}) )
    r.exit()
    
def test3():
    from redeem.Redeem import main
    main()
    
def test4():
    test_str = """
        G28
        G0 Z20
        G92
        G1 Z0.350 F5000.000
        G1 X-100.0 Y-100.0 F5000.000
        G1 X100.0 Y-100.0
        G1 X100.0 Y100.0
        G1 X-100.0 Y100.0
        G1 X0.0 Y0.0
        """
    r = Redeem()
    g = r.printer.processor
    for line in test_str.splitlines():
        if line:
            print line
            g.execute( Gcode({"message": line, "prot": "Test"}) )
        
    r.exit()

if __name__ == "__main__":
    test_redeem()

