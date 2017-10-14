Redeem
======

Redeem is the Replicape firmware; it is a daemon process that chews G-codes
and spits out coordinates. The software can be found in the redeem repository:
https://github.com/intelligent-agent/redeem

Architecture
------------

Most of Redeem is written in Python, with the exception of the most
heavily used gcode commands: G0/G1. These have been optimized in C.
This allows rapid development of new features which are infrequently
run -- such as bed leveling -- using python's scripting language capabilities
of garbage collection and extensive libraries


..  figure:: media/redeem_stack.png
    :figclass: inline

Installation
------------

The recommended method for installation is to use the Umikaze image which includes
operating system, redeem, octoprint and all the dependencies needed.

from Package
~~~~~~~~~~~~

If you'd rather install the Redeem firmware on your own operating system, you can use
the Debian repository packages for Replicape and Toggle:

::

    wget -O - http://kamikaze.thing-printer.com/apt/public.gpg | apt-key add -
    echo "deb http://kamikaze.thing-printer.com/apt ./" >> /etc/apt/sources.list
    apt-get update

from Source
~~~~~~~~~~~

enable kernel repo: http://repos.rcn-ee.com/(debian|ubuntu)

::

    apt-get install am335x-pru-package pru-software-support-package swig python-smbus
    mkdir -p /usr/src
    cd /usr/src
    git clone https://github.com/intelligent-agent/redeem.git
    cd redeem
    make install
    mkdir -p /etc/redeem
    cp configs/* /etc/redeem
    cp data/* /etc/redeem




Updating
--------
..  versionadded:: 2.0.5

The octoprint\_redeem plugin should provide a prompt when there is a
redeem update available, and the wizard should work in almost all cases.
If it doesn't, or if you prefer knowing the gritty details of how to do
this by hand, here are the manual instructions:

login as root and execute these commands:

::

    cd /usr/src/redeem
    git pull
    python setup.py clean install
    cp configs/* /etc/redeem
    systemctl restart redeem


Develop branch
--------------
..  versionchanged:: 2.0.5

If your printer suffers from problems that are being addressed or if you
want to help test the next version of redeem, you need to switch your
installation to the develop branch of Redeem. **Beware: there be bugs
and dragons in this code!**

To do so, follow these instructions:

::

    cd /usr/src
    rm -r redeem
    git clone https://github.com.com/intelligent-agent/redeem.git
    cd redeem
    git checkout develop
    make clean install
    systemctl restart redeem
