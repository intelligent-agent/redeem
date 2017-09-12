Connecting
==========

Browser
-------

Umikaze uses Octoprint for interacting with the Replicape and your 3D printer.

To access, go to `http://kamikaze.local`__.

__ http://kamikaze.local

If you cannot connect, read the section on :doc:`/support/howto/linklocal`.

Terminal
--------

Sometimes it is necessary to make changes to the configurations directly
or to debug a broken config file, without going through the OctoPrint browser
interface. For those unfamiliar with working with a linux operating system,
check out our :doc:`/support/howto/beginlinux`.

Connecting via Network
~~~~~~~~~~~~~~~~~~~~~~

::

    ssh root@kamikaze.local


Connecting via USB
~~~~~~~~~~~~~~~~~~

The BeagleBone has ethernet over USB that has a static IP
address of 192.168.7.2. Connect your host computer to the device and then
log in with::

    ssh root@192.168.7.2

Access Control
--------------

There are two user accounts that have admin permissions:

- username: ``root``, password: ``kamikaze``
- username: ``ubuntu``, password: ``temppwd``

..  danger::
    If you are not on a secure or private network, it is highly recommended
    to :ref:`change the password <ChangePassword>` for both accounts. Someone
    accessing your device can intentionally (or unintentionally) damage your
    3D printer.

..  note::

    These user passwords are completely separated from the
    octoprint users you setup during the setup wizard for access control.



