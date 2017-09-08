
Configuration
=============

Now you're looking at how to setup Redeem and calibrate it to your
printer's hardware. This section isn't exhaustive yet, if you need this
page to add a specific section about something, go ask for it by
reaching out in the `community
section <Replicape:_Getting_Started#Getting_Support>`__

If you have your BeagleBone plugged into the network, you can connect a
monitor and keyboard to get the IP address assigned to the board when it
boots. When the stack boots, you will see the Toggle interface (you will
need to rotate your monitor to portrait mode to make it easier to work
with. Assuming you're running Kamikaze 2.0.8 or higher, you can hit
Alt-F2 on the keyboard to change to another terminal, then log in with
the username **ubuntu** and the password **temppwd**. Once logged in,
enter **ipconfig eth0** and you will see the IP address in the
information. Use that IP to connect via web browser to get to OctoPrint.


Basic
-----

For physical wiring of the board `go
here <http://wiki.thing-printer.com/index.php?title=Replicape_rev_B>`__.
Once the board is wired and powered, you can connect to OctoPrint via a
web browser.

Once you connect to the OctoPrint interface, you will need to step
through setup the first time. As you step through the setup:

-  Set a username and password for OctoPrint
-  It's recommended that you keep Access Control Enabled for security
   reasons.
-  Set your print bed dimensions
-  Axis speeds can be left at the defaults, as they only control the
   manual movements that you make through OctoPrint.

To start with, go look at Elias' `video on getting
started <https://www.youtube.com/watch?v=BKb28fJx26I>`__. The redeem
repository he's talking about in the video is found
`here <https://bitbucket.org/intelligentagent/redeem>`__


End Stops
---------

In case you missed it, check Elias' `youtube video on endstops <https://www.youtube.com/watch?v=5LEjdQtIYe4>`__.
