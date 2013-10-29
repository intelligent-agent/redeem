    :::python
     _____           __
    | ___ \         | (_)
    | |_/ /___ _ __ | |_  ___ __ _ _ __   ___
    |    // _ \  _ \| | |/ __/ _  |  _ \ / _ \
    | |\ \  __/ |_) | | | (_| (_| | |_) |  __/
    \_| \_\___| .__/|_|_|\___\__,_| .__/ \___|
             | |                 | |
             |_|                 |_|

Replicape is a 3D printer cape for BeagleBone.  
Hardware features:  
-   5 stepper motors (2.5A DRV8825) (X, Y, Z, Ext1, Ext2)  
-   3 high power MOSFETs (PWM controlled) for 2 extruders and 1 HPB.  (12..24V)  
-   3 medium power MOSFETs (PWM controlled) for up to 3 fans/LED strips.  (12V)  
-   3 analog input ports for thermistors. noise-filtered inputs and option for shielding  
-   6 inputs for end stops (X, Y, Z).  
-   1 bus for Dallas 1W temperature sensor for monitoring the cold end. Up to 10 sensors can be added to the bus.  
-   Programmable current limits on steppers motor drivers (SMD). No need to manually adjust a pot meter.  
-   Microstepping individually programmable for each SMD from 1 to 32.  
-   All steppers are controlled by the Programmable Realtime Unit (PRU) for hard real time operation.  
-   Option for stackable LCD cape (LCD3). HDMI compatible LCD on the way.  
-   Single 12 to 24V PSU, fans are still 12V.  
-   Comptabile with BeagleBone and BeagleBone Black.  
-   Open source hardware and software.  
-   Software written in Python for maintainability and hackability.  
  
Software features:  
- Accelleration with corner speed prediction.  
- Printer settings loaded from file (Version 0.4.2)  
- Controllable via ethernet, USB, printer display.   

TODO for software:  
- Make a fancy GUI with 3D model  
- Implement realtime slicing on BeagleBone so an STL file can be sent directly (very cool, Koen is working on this).  
- Better axis max-speed. It now limits the feed rate, but should instead take into account the speed in a given direction.  
- PID autotune.  
- Constant jerk.  

Known issues:  
- USB hugs all CPU, disabled for now. Use ethernet (over USB) instead.  

Fixed issues:  
- Optimize the merging of timings from the different steppers.(Fixed in verison 0.5.0.)  
- Long stretches of stepper movement that occupies more than the available 40K of memory are not cheked and 
kills the whole shebang. Must be fixed. To reproduce, try moving the Z-axis 20cm.   
- Temperature sometimes not available. (OK now, checks multiple times if not available. Fixed in 0.5.3)  
- Implemented axis max-speed, configurable from the settings-file.   
- When slicing with slic3r, the printhead often stops to "think" (before shifting Z etc). This happens even though the PRU is pull of commands.(It was since G92 was not buffered)  
- The amount of available DDR memory for the PRU shrinks causing the program to crash for unbuffered commands. By logging the amount of available PRU memory used during a print, the amount availabe at the end of the print is not 0x40000 and pru.wait_untill_done() never returns. This could be eith due to skipped events or wrong memory reporting in the commit_data() function of the PRU. The print should still finish as expected, though.  
- Better temperature control. Temperature control was coarse due to a badly written ADC driver fetching old values. Fixed and patch sent in.  

Blog: http://hipstercircuits.com  
Wiki: wiki.replicape.com  
