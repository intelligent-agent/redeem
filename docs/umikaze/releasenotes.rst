Release notes
=============

`Umikaze 2.1.1 <release_notes_Umikaze_2.1.1>`__

Release notes for previous versions:

`Release notes for Kamikaze
2.1.0 <https://github.com/goeland86/Umikaze2/releases/tag/2.1.0>`__

..  note::

    The size is 835 MB compressed, but expands to a 3.6GB partition,
    suitable for a 4GB or bigger SD card. If you have one of the
    older rev C BeagleBone Black with only 2GB eMMC, you will not be able to flash
    it, and will need to run from the SD card.

*More Release Notes Here*

Source
------

Umikaze 2.1.x is a distribution building on top of the wonderful Ubuntu
LTS console distribution for BeagleBone. It is merely adding the
necessary packages and overlays necessary as in 1.x and 2.0.x versions
did on top of Debian. Kamikaze 2 source files are available here
`Source files <https://github.com/goeland86/Umikaze2>`_

Upgrade From 2.1.0
------------------

Since this is a Debian system, packages can be upgraded with apt.

::

    apt-get update
    apt-get upgrade

Please note that since this also upgrades the SSH daemon, which may kick
the user out during the upgrade process. If that happens, you need to
SSH back in, and continue the process:

::

    dpkg --configure -a

Most users will want to update the latest version of redeem or toggle
periodically.

Upgrade from 2.0.8
------------------

*More Instructions here*

Bugs
----

Follow the Umikaze development here: `Umikaze
github <https://github.com/goeland86/Umikaze2/>`__

There are always bugs, and we're hard at work squashing them. If you run
into a bug, please check the `Umikaze github
bugtracker <https://github.com/goeland86/Umikaze2/issues>`__ to see if
it's been reported, and if not, please add it there so it can be tracked
by other users also.

