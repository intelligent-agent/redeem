Toggle
======

additional sections:

- what is toggle?
- how do i install manually?


Update
------

Just like Redeem's updates, the octoprint\_toggle plugin should provide
a wizard for updating the software. Below are the manual commands for
the geeks, the curious, and those whose automatic updates failed. But
please report it if the failure is consistent!

login as root and execute these commands:

::

    cd /usr/src/toggle
    git pull
    python setup.py clean install
    cp configs/* /etc/toggle
    systemctl restart toggle
