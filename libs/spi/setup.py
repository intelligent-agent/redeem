#!/usr/bin/env python

from distutils.core import setup, Extension

from distutils import sysconfig
import re

vars  = sysconfig.get_config_vars()
for v in vars:
	if str(vars[v]).find("--sysroot") > 0:
		vars[v] =  re.sub("--sysroot=[^\s]+", " ", vars[v])

setup(	name="spi",
	version="1.1",
	description="Python bindings for Linux SPI access through spi-dev",
	author="Volker Thoms",
	author_email="unconnected@gmx.de",
	maintainer="Volker Thoms",
	maintainer_email="unconnected@gmx.de",
	license="GPLv2",
	url="http://www.hs-augsburg.de/~vthoms",
	include_dirs=["/usr/include"],
	ext_modules=[Extension("spi", ["spimodule.c"])])

