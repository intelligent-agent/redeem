Updating
========

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

If your printer suffers from problems that are being addressed or if you
want to help test the next version of redeem, you need to switch your
installation to the develop branch of Redeem. **Beware: there be bugs
and dragons in this code!**

To do so, follow these instructions:

::

    cd /usr/src
    rm -r redeem
    git clone https://bitbucket.org/intelligentagent/redeem.git
    cd redeem
    git checkout develop
    make clean install
    systemctl restart redeem