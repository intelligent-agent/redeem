GCode command plugin system
===========================

The GCode plugin system allows dynamic loading of new GCode commands without changing a single line of code in the Redeem system.

How to add a new command
------------------------

1. Create a new file in the gcodes/ directory with the name of your GCode command and the **py** extension. (like M106.py).
2. Fill the file with the following template and change it to fit your needs. You have to change the **<GCodeName>** with your GCode name (e.g. M106):

        """
        GCode <GCodeName>
        <GCode description>

        Author: <author>
        email: <email>
        Website: <website>
        License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
        """

        from GCodeCommand import GCodeCommand
        import logging

        class <GCodeName>(GCodeCommand):

            def execute(self, g):
                #Put your GCode execution commands here. You have access to the self.printer object to control the printer


            def get_description(self):
                return "<GCode description>"

3. Create a file in the tests directory named test_<GCodeName> with the following template:

        """
        GCode <GCodeName>
        <GCode description>

        Author: <author>
        email: <email>
        Website: <website>
        License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
        """
        import unittest

        import sys
        sys.path.insert(0, '../redeem')
        
        class <GCodeName(unittest):
        
            """
            The following tests check that the path object that is sent to self.printer.path_planner
            matches what is expected, for [several variants of] each Gcode command
            """
        
            def test_execute(self):
        
        
            def test_get_description(self):
                
        #TODO - (If possible, list the following)
                Working examples of the gcode and short description of action expected.
                List a few edge cases (one that should work, one that should fail).
                List a few cases that should obviously fail.
        """
                

4. Restart Redeem. You command should be ready to be used.

