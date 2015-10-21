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

3. Restart Redeem. You command should be ready to be used.