WiFi
====

Umikaze 2.1 uses NetworkManager for handling connections, instead of
connman.

Basically plug in your wifi dongle, boot (or reboot), connect to the BBB
via USB or Ethernet, login via SSH as root, and run

::

    nmtui

The wizard should be pretty self-explanatory, but reach out to the
community on Google+ or the #support channel on Slack should you need
help.