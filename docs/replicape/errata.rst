Errata
======

Rev B3
------

The first batch revision is Rev B3

- Power save mode is not implemented correctly. Therefore there will be some 3 seconds of noise from the steppers until u-boot can configure the SPI registers correctly.
- Some boards have shipped without the EEPROM flashed. To fix that: :ref:`EEPromFlash`

Rev B2
------

Replicape Revision B2 has a hardware error. This board was only
manufactured for beta testing and has “developer edition” clearly shown
on the board. The error is that 470K resistors were mounted instead of
4.7K for the thermistor voltage divider. The resistors were manually
changed to 5.1K resistors. The thermistor voltage divider resistance
value is changed in software to reflect this.
