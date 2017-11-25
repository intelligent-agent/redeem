Z Probes
========


Z Probes are a great addition to the 3d printer! Having said that they
do not take the place of careful initial manual config. For Delta
printers they can be helpful for the calibration procedure but again
they will not solve a badly built printer. I would suggest you should
have your printer in a basic configured state.

First steps For a circular bed use : G29C #to create a macro for you(
look at the wiki for details on it usage) M500 # to save to your
local.cfg

For a rectangle bed use G29S # to create a macro for you( look at the
wiki for details on it usage) M500 # to save to your local.cfg

Edit the local.cfg and add the appropriate G31 and G32 Macro.

::

    G32       some Macro examples:

    G32 =
         M106 P2 S255                    ; Turn on power to probe.
    G32 =
         M574 Z2 x_ccw,y_ccw,z_ccw    ; enable Z2 endstop
    G32 =
        M280 P0 S-60 F3000              ; Probe down (Undock sled)

    G31       some Macro examples:

    G31 =
         M106 P2 S0                        ; Turn off power to probe.
    G31=
         M574 Z2                         ; disable Z2 endstop
    G31 =
        M280 P0 S320 F3000              ; Probe up (dock sled)

The same procedure as endstops First make sure your Z probe triggers the
endstop Next make sure the Z probe stops motion (refer to endstop
section for more detail.) Set your Z probe travel speed ...slow it down
until your sure it works correctly. Test and happy probing!
