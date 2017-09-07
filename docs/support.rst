Getting Support
===============

The Replicape/Redeem community is mostly active in three places:

-  `The Replicape
   Slack <http://www.thing-printer.com/wp-login.php?action=slack-invitation>`__
-  `IRC on #replicape
   (irc.freenode.net) <https://webchat.freenode.net/>`__
-  Google+ community:
   `Thing-printer <https://plus.google.com/communities/104577360369030938514>`__



Redeem's and Kamikaze's pages are pretty complete already, you're here
reading sort of a “where do I find information about specific topics?”

The answer is:

-  `Replicape's <Replicape_rev_B>`__ page for anything to do with
   hardware connections (wiring, outputs, etc.)
-  `Redeem <Redeem>`__'s page for anything to do with what features the
   software holds, and what G and M-codes do
-  `Kamikaze <Kamikaze>`__'s page for anything regarding the Kamikaze
   image, including the latest release link for Kamikaze (network,
   updates, etc).
-  `The Marlin to Redeem <Marlin_to_redeem>`__ guide, helping those of
   you coming from Marlin appreciate what the differences in Redeem are
   and why.



Linux Beginner? Help is here
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To those of you new to the Linux environment, here are a few steps I
would recommend some to read up on a few `basic linux
skills <http://manuals.bioinformatics.ucr.edu/home/linux-basics>`__

Also, if you find that redeem fails to start, and there's nothing
obvious in the log you get out of octoprint, that might mean there's a
typo in one of your config files. To see where, run **systemctl status
-n 100 redeem** on your BBB, it should point you straight to what you
need to change.