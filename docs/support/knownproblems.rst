Known problems
==============

-  Redeem configuration files list is empty on initial boot.

   -  Upload an empty config file to show the pre-defined files from the
      filesystem.
   -  Same applies to Toggle

-  Uploading local.cfg via Octoprint Redeem plugin renders an empty file
   the first time.

   -  Upload the file twice for it to work.

-  The Kamikaze logo does not show up on MangaScreen during eMMC
   flashing. Purely cosmetic.
-  Some modifications of the local.cfg or to a printer's .cfg file
   aren't applied

   -  The workaround is to manually search for and delete two files:

`` firmware_endstops.bin ``

and

`` firmware_runtime.bin``

they should be somewhere in /usr/local/lib/python2.7 and you can find
them with sudo find \| grep firmware\_runtime in that directory.