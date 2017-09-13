Toggle
======

..  figure:: ./media/toggle_header.png
    :figclass: inline


..  contents:: Table of Contents
    :depth: 2
    :local:

Toggle is the front end software used to slice, dice and print the stuff
you want made. It's in its infancy, but if you want to contribute, here
is the repository: https://bitbucket.org/intelligentagent/toggle

Toggle does not depend on any window system, but instead renders
directly to the framebuffer. This keeps the overhead low and keeps the
necessary graphics packages to a minimum. For building the UI,
`Clutter <https://developer.gnome.org/clutter/stable/>`__ is used which
relies on `Cogl <https://developer.gnome.org/cogl/stable/>`__ as a
backend for communicating with EGL and GLES2. For standard widgets
(buttons etc) either GTK+3 is used or
`mx <https://github.com/clutter-project/mx>`__ . `Gobject
introspection <https://wiki.gnome.org/action/show/Projects/GObjectIntrospection?action=show&redirect=GObjectIntrospection>`__
is used for making bindings to Python.

..  warning::

    This is very much a work in progress and not even alpha-testable. The project is just getting started.

Software installation
---------------------

Debian
~~~~~~

Toggle now comes wrapped up in a tight little package for Debian. It is
also included in the `Kamikaze <Kamikaze>`__ image for use with
`Replicape <Replicape>`__. For the latest development version, have a
look at the `https://bitbucket.org/intelligentagent/toggle Toggle
repository <https://bitbucket.org/intelligentagent/toggle_Toggle_repository>`__.
the package is called toggle, but you also need libtoggle to make it
work::

    sudo apt-get install libtoggle toggle

Angstrom
~~~~~~~~

Toggle is included in the latest Thing image: http://wiki.thing-printer.com/index.php?title=Thing

Make sure you have the thing-printer feed added an your BeagleBone::

     echo 'src/gz replicape-base http://feeds.thing-printer.com/feeds/v2014.06/ipk/eglibc/armv7ahf-vfp-neon/machine/beaglebone/' > /etc/opkg/replicape-base.conf

Then::

    opkg update
    opkg install toggle

Configuration
-------------

Default configuration

::

    [System]
    # CRITICAL=50, # ERROR=40, # WARNING=30,  INFO=20,  DEBUG=10, NOTSET=0
    loglevel =  20

    stylesheet = /etc/toggle/style/style.css
    ui = /etc/toggle/style/ui.json
    plate = /etc/toggle/platforms/prusa.stl
    model_folder = /usr/share/models
    message_fd = /dev/toggle_1

    rotation = 90
    angle_min = -50
    angle_max = 50
    scale_min = 0.5
    scale_max = 3.0

    filter_events = false

    [Geometry]
    width = 0.2
    height = 0.2
    depth = 0.2

    [Preheat_start]
    0 = M117 Heating...
    1 = M106 P1 S255
    2 = M190 S65
    3 = M109 S220

    [Preheat_stop]
    0 = M117 Stopping heating
    1 = M190 S0
    2 = M109 S0

    [Rest]
    api_key = 934A6B7A51B34445A6A5A51DA96713A3

Software stack overview
-----------------------

Toggle builds on Clutter as the main software toolkit, with help from Mx
for making the buttons and layout and Mash for importing the STL models.
Clutter in turns relies on Cogl for interfacing with the actual
3D-engine in the BeagleBone Black. The interface to the 3D engine is
copyrighted by Imagination Technologies and so it is one of the very few
components that are not open source in this image. Texas Instruments is
the only ones that have access to this code, so we are reliant on them
making the drivers for various window managers. So far, none are
available, neither X nor Wayland, so we are stuck with the null window
system. That is not really a problem, since it makes stuff go fast, but
it does require compilation of each of the packages marked in blue in
the figure below to be compiled in a non-standard (from the Debian
distro) way. Having a null window system adds a lot of restrictions on
which toolkit can be used when wanting a mixed 2D/3D app. Clutter is one
of them, and I think Qt is an alternative. The main Toggle user
application is written in Python using G-object Introspection for
interfacing with the lower level libraries. The engine in the BeagleBone
Black is the SGX530, and you can do some pretty cool stuff with it.
Spec-wise it is similar to what sits in the iPhone 4 (SGX535), but
without the OpenGL (only OpenGL ES2.0) capabilities.

..  figure:: media/toggle_stack.png
    :figclass: inline

Compiling on BBB
----------------

In order to compile Cluttter projects directly on the BBB instead of on
the host, you need to install the dev packages. There are some quirks
due to a file conflict between g-ir-host-dev (which should not be
installed at all) and libgirepository-1.0-dev::

     opkg install libclutter-1.0-dev --force-overwrite
     opkg install systemd-dev
     opkg install libmx-2.0-dev
     opkg install libmash-0.2-dev

Clone the toggle repo::

     cd /usr/src
     git clone https://intelligentagent@bitbucket.org/intelligentagent/toggle.git
     cd toggle
     export CC=arm-angstrom-linux-gnueabi-gcc
     make

Introspecting on BBB:

    cd /usr/src/toggle/toggle-plate
     make
     make install
     python
     from gi.repository import Toggle, Clutter
     Clutter.init()
     Toggle.Plate()

Debug output
~~~~~~~~~~~~

::

    systemctl status -n 100 toggle

Overview
--------

Toggle relies on a few libraries and tool kits, but since it is designed
for embedded platforms, the dependencies are kept fairly low in
comparison with X-based or Wayland-based applications. Here is a quick
overview of the dependencies of Toggle. These libraries have now got
debian based (.deb packages) and Angstrom based (.opkg packages)
available.

Contributing
------------

Contributions are highly welcome! Here's what you do:

#. Fork the repository (on your host machine):
   https://bitbucket.org/intelligentagent/toggle
#. Make changes
#. Upload the file from your host to your BeagleBone to verify that it
   works.
#. Push the changes to your local repository
#. Make a pull-request.
#. If the request goes through, the software is updated and a new
   package is made.
#. (optional) Blog about it so other users can upgrade and get your
   changes : )

Old sketch of how it should look
--------------------------------

..  figure:: media/toggle_sketch.jpg
    :figclass: inline




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


