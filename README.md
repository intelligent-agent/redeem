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
Features include:  
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
  
TODO for software:  
+ Optimize the merging of timings from the different steppers.(Fixed in verison 0.5.0.)  
- Make a fancy GUI with 3D model  
- Implement realtime slicing on BeagleBone so an STL file can be sent directly (very cool, Koen is working on this).  
- Better temperature control. It's a little coarse.  
- Implement axis max-speed and make it configurable from the settings-file.   

Software features:  
+ Printer settings loaded from file (Fixed in version 0.4.2)  
- Controllable via ethernet, USB, pipe or GUI. (Bug: USB hugs all CPU)  

Known issues:  
- Long stretches of stepper movement that occupies more than the available 40K of memory are not cheked and 
kills the whole shebang. Must be fixed. To reproduce, try moving the Z-axis 20cm.   
- Temperature shows 0 deg. when not contact with the driver.   

Blog: http://hipstercircuits.com  
Wiki: wiki.replicape.com  
