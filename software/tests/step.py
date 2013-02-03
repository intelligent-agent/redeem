#!/usr/bin/env python

from spi import SPI

spi2_1 = SPI(2, 1)
spi2_1.bpw = 8
spi2_1.mode = 0
spi2_1.writebytes([0x30])

