Linux Beginner Guide
====================

Windows Users
-------------

To ``ssh`` on Windows, it is recommended to use `PuTTY`__

__ http://www.putty.org/


To those of you new to the Linux environment, here are a few steps I
would recommend some to read up on a few `basic linux
skills <http://manuals.bioinformatics.ucr.edu/home/linux-basics>`__

Also, if you find that redeem fails to start, and there's nothing
obvious in the log you get out of octoprint, that might mean there's a
typo in one of your config files. To see where, run **systemctl status
-n 100 redeem** on your BBB, it should point you straight to what you
need to change.

.. _ChangePassword:

Changing Password
-----------------


Do this by SSH-ing in as the user you want to change the password of and running the command:

::

    passwd

Helpful SSH Commands
--------------------

Starts a log within the terminal:

::

    sudo journalctl -fl ;


Open network control panel:

::

    sudo nmtui

Restarts Redeem:

::

    sudo systemctl restart redeem

Shows which version of Kamikaze is installed:

::

    cat /etc/kamikaze-release


Show status of Toggle:

::

    systemctl status toggle -l -n 100
