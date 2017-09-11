Replicape
=========

..  figure:: ./images/replicape_header.png
    :figclass: inline

..  contents:: Table of Contents
    :depth: 2
    :local:

Replicape is a high end 3D-printer electronics package in the form of a
Cape that can be placed on a BeagleBone Black.

This page is about the major revision B. For documentation on previous version: `Revision A </2.0.8/replicape.html>`_.

It has five high power and low noise stepper motors
with cool running MosFets and it has been designed to fit in small
spaces without active cooling and without the need for physical access
to the board once installed. That means no potentiometers to trim or
switches to flip.

This page is about the hardware. It explains how to install the board
and wire everything up. If you are looking for software that will run,
have a look at the :doc:`/kamikaze` CNC image. There are other
options as well, but that is the standard that will work for most
people.

Availability
------------

There has been a `Kickstarter for Replicape Rev B`__.
Since the Kickstarter is done, Replicape Rev B can be ordered from the `thing-printer web`__ shop.

__ https://www.kickstarter.com/projects/1924187374/replicape-a-smart-and-quiet-3d-printer-control-boa
__ http://www.thing-printer.com/product/replicape/

Mounting the Replicape on the BeagleBone
----------------------------------------

As the name suggests, Replicape is a cape. Capes are one of the defining
things about BeagleBone black/white/green, where the main development
board acts as a base unit, and then accepts different add-on hardware
through the two 48 pin headers, which in turn define some of the pin
behaviors during Linux kernel startup. This is similar to “shields” on
Arduino and “HAT”s on Raspberry Pi. Mounting the Replicape on BeagleBone
should be pretty straight forward, just make sure the notch in the cape
goes around the Ethernet connector so it makes a.. cape!

How to wire up the board
------------------------

Fritzing example
~~~~~~~~~~~~~~~~

The Fritzing board below shows the most basic setup for connecting the board.

..  figure:: ./images/replicape_b3.png

Connector overview
~~~~~~~~~~~~~~~~~~

..  figure:: ./images/replicape_bla.png

Steppers
--------

Bipolar and hybrid stepper motors are supported with these stepper motor
drivers (SMD). Some smaller stepper motors are known to produce a high
pitch noise and get very warm even with a low current setting. They will
appear to work, but they may very well burn do to the large heat being
produced.

| With the board oriented as in the above image, the wires for the
  steppers are:
| Rev B2: **1, 2, 3, 4 = OB1, OA1, OA2, OB2**\ <- Not so standard
| Rev B3: **1, 2, 3, 4 = OA2, OA1, OB1, OB2**\ <- Pretty standard

Noise
-----

The TMC2100 stepper drivers are designed to be very quiet. However, if
the coil resistance on the steppers are too high, the current limit on
the stepper drivers are never reached, and this makes the steppers give
off a very high pitch sound. If you are experiencing high pitch noise,
you might want to experiment with the “stealth mode” which will silence
all steppers. This is micro stepping level 7 and 8. Stealth mode might
make the steppers somewhat less powerful, but should work for most
printers. To calculate if the current limit is reached or not, you can
calculate the maximum coil resistance for a given input voltage. If the
input voltage is 12V and you want to run your steppers on 1A current
limit, the maximum coil resistance can be 12 ohm.

Heaters
-------

The heater output on the Replicape have rugged connectors, with the heat
bed having double connectors for redundancy (in case one wire comes
loose) and for handling the power load. These are brand Molex connectors
that have both screw terminals for easy fitting and slot in connectors
for easy disassembly. All the heaters are controlled with PWM. The power
MOSFETs controlling the output are AON6758 that are rated at 30V, 32A.
For a 12V PSU, this means that the maximum power that can be used on the
heated bed is 32 A x 12 V = 384 W. Please remember that there is a 20 A
fuse preventing such a large power use on the heated bed. The 20 A fuse
is installed to keep the traces on the PCB from over heating.

Thermistors
-----------

The thermistor inputs on Replicape have been designed for 100 K NTC
thermistors. These are the typical type used for desktop 3D-printers.
10K thermistors can also be used, however the voltage divider setup
makes the 100 K thermistors more ideal since the area of most change
will be around 100 degrees. TODO: add charts for 10 K and 100 K
thermistors showing their ideal temperature for most significant bit
change.

Thermocouple
------------

Thermocouple is not supported out of the box, but instead requires some
extra care in order to work. Most importantly is to use a `voltage
divider <https://en.wikipedia.org/wiki/Voltage_divider>`__ on the signal
so it is converted to a value that the analog input on the BeagleBone
can handle: 1.8V. Secondly, the input needs to be sent in on AIN0..AIN3,
which are pins P9\_37...P9\_40. Then, the analog input used needs to be
enabled by a device tree overlay, ideally by editing the current DTO.
That can be found here: https://github.com/eliasbakken/bb.org-overlays.
Finally, the software needs to be hacked to make use of the new analog
input and conversion.

Inductive sensors
-----------------

Inductive sensors are typically mounted on the end stop marked Z2. If
you have an NPN (sinking) sensor, you can mount it directly on there.

Typically
| Brown: 12V (pin 4)
| Blue: GND (Pin 2)
| Black: Sig (Pin 1, square)

If you have a PNP (sourcing) type, you need to add a pull-down
resistor externally between the signal and ground on the sensor. The
value is not important, as long as it can comfortably pull a 4.7K
resistor low. 1K should be fine.

DS18B20 temperature sensors
---------------------------

The connector marked Dallas W1 can be used for connecting temperature
sensors of the type DS18B20. These are relatively low temperature
sensors that can handle up to 125 degrees Celsius and are typically used
for monitoring the cold end of the extruder which should never reach
more than around 60 degrees when printing with PLA. The great thing
about using a cold end monitor is that the temperature measurements can
be used to regulate the fan on the extruder. That way, the noise level
can be lowered further than when using the thermistor as a trigger for
enabling the extruder fan.

Switches as end stops
---------------------

All the end stops have 4.7K (47K on Rev B3) pull-up resistors on the
signal lines. Therefore, the best way to connect switches is between the
signal and ground pins on the connectors. If the switches have can be
connected as normally closed (NC), that is preferable since it will act
as a pressed in switch if a cable has been destroyed or removed.

The signals on the end stops as as follows:
| pin 1, square, signal (yellow wire in Fritzing diagram above)
| pin 2, round, GND (black wire in Fritzing diagram above)
| pin 3, round, VCC (red wire in Fritzing diagram above)(5V)

Connectors
----------

Replicape comes with Molex screw terminals for the heaters, hot bed
and power input. Most stepper motors comes with the 4 pin Molex 2.54 mm (0.1")
female connector attached. Fans and end stops sometimes
comes with the right connector, but not always, it depends on the
manufacturer. The white 2, 3 and 4 pin connectors on Replicape used
for thermistors, end stops and steppers are the MTA-100 series from TE
connectivity:

| **2 pin**
| For the 2 pin thermistor inputs and fan outputs:
| https://www.digikey.com/product-detail/en/640455-2/A19450-ND/258997
| Here is a couple of good mating products:
| http://www.digikey.com/product-detail/en/1375820-2/A99613-ND/1864915
| http://www.digikey.com/product-search/en?keywords=952-2227-ND

| **3 pin**
| For the 3 pin end stop and Dallas 1W inputs:
| https://www.digikey.com/product-detail/en/640455-3/A19451-ND/258998
| Mating alternatives:
| https://www.digikey.com/product-detail/en/1375820-3/A99614-ND/1864916
| http://www.digikey.com/product-search/en?keywords=952-2228-ND

| **4 pin**
| For the 4 pin stepper motor connectors, and the inductive sensor input:
| https://www.digikey.com/product-detail/en/640455-4/A19452-ND/258999
| Mating alternatives:
| http://www.digikey.com/product-detail/en/1375820-4/A99615-ND/634994
| http://www.digikey.com/product-search/en?keywords=%09952-2229-ND

Power
-----

Replicape is powered through a single 12 to 24 V power supply. This
powers the BeagleBone as well, through a 5V step down converter. It also
supplies 12V for fans and the inductive sensor. If the USB device
connector is used, no power is drawn through the connector.

**Note** that if you do not power the Replicape, the BBB will not be
able to properly communicate with it, and you will get an error such as

``kamikaze redeem[675]: Error accessing 0x70: Check your I2C address``

Hardware source files
---------------------

If you want to extend, build or modify Replicape, for the repository:
https://bitbucket.org/intelligentagent/replicape

**Routing and noise**

The Rev B PCB is a four layer PCB. The top layer is mostly vertical
traces and the bottom layer is mostly horizontal. The uppermost inner
layer is a ground layer with no signal traces. The lower inner layer
is the voltage plane layer. There are in total 4 voltage planes:
12..24V, 12V, 5V and 1.8V. In addition, there is a 3.3 V trace routed.

**Component placement**

All components are placed on the top layer to reduce cost of
manufacturing. There are two fiducials on the top side to aid in pick
and place placement of components.

**Board extensions**

Revision B does not have a dedicated extension header like the one
that was introduced in rev A4A. There should still be possible to add
an extension board on top of the current version that can add up to
three more extruders. This is being developed.

Hardware details
----------------

**Pins on the BeagleBone used by replicape**

Below is a diagram of the pins that have been used on the BeagleBone.

..  figure:: ./images/replicape_pinout_rev_b3.png
    :figclass: inline


**Stepper Motor Controllers**

There are 5 Stepper Motor Controllers (SMDs) of the type `TMC2100 datasheet`__
on Replicape. With the right stepper motors, they reduce the noise
level a lot compared to other, similar type SMDs. The peak current is
rated at 2.5 A, with an RMS current pr phase of 1.2 A. TMC2100 has
over temperature protection. If skipped steps occur, it might be due
to over heating. To distribute heat better, there are exposed areas
directly under the stepper drivers where heat sinks can be mounted. In
that case, you may want to consider adding active cooling to lead the
air flow away from the gap between the BeagleBone and the cape.

__  http://www.trinamic.com/products/integrated-circuits/stepper-power-driver/tmc2100

**High power MOSFETs**

3 X `SIRA34DP-T1-GE3 <http://media.digikey.com/pdf/Data%20Sheets/Vishay%20Siliconix%20PDFs/sira34dp.pdf>`_
| Maximum voltage: 30V
| Maximum current: 40A

**Low Power MOSFETs**

| 4X AO7400
| Maximum voltage: 30 V
| Maximum current: 1.7 A


**Thermistor inputs**

The thermistor inputs have a first order low pass filter with a cut
off frequency of 3.4 Hz. Since only slow moving signals are measured,
this cuts out all capacitive influence from the high power heater
cables that typically run in parallel with the thermistor cables.

**Power management**
Replicape has two step down voltage regulators or 5V and 12V, both
built using Richtec RT8268GFP.

Update EEPROM
-------------

The EEPROM on the Replicape should be updated when it arrives. If not, here are the instructions on how to update it.

.. _EEPromFlash:

Debian
~~~~~~

On the Debian/kamikaze image::

    sudo -s
    wget https://bitbucket.org/intelligentagent/replicape/raw/bf08295bbb5e98ce6bff60097fe9b78d96002654/eeprom/Replicape_00B3.eeprom
    cat Replicape_00B3.eeprom > /sys/bus/i2c/drivers/at24/2-0054/at24-1/nvmem
    exit

Errata
------

Rev B3
~~~~~~

The first batch revision is Rev B3

- Power save mode is not implemented correctly. Therefore there will be some 3 seconds of noise from the steppers until u-boot can configure the SPI registers correctly.
- Some boards have shipped without the EEPROM flashed. To fix that: :ref:`EEPromFlash`

Rev B2
~~~~~~

Replicape Revision B2 has a hardware error. This board was only
manufactured for beta testing and has “developer edition” clearly shown
on the board. The error is that 470K resistors were mounted instead of
4.7K for the thermistor voltage divider. The resistors were manually
changed to 5.1K resistors. The thermistor voltage divider resistance
value is changed in software to reflect this.
