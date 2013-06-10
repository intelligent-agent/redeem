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
-   1 optional Dallas 1W temperature sensor for monitoring the cold end.  
-   Programmable current limits on steppers motor drivers (SMD). No need to manually adjust a pot meter.  
-   Microstepping individually programmable for each SMD from 1 to 32.  
-   All steppers are controlled by the Programmable Realtime Unit (PRU) for hard real time operation.  
-   Option for stackable LCD cape (LCD3). HDMI compatible LCD on the way. 
-   Single 12 to 24V PSU, fans are still 12V  
-   Comptabile with BeagleBone and BeagleBone Black  
-   Open source hard ware and software  
-   Software written in Python for maintainability and hackability  
  
Blog: http://hipstercircuits.com

TODO for software:  
- Optimize the merging of timings from the different steppers.  
- Make a fancy GUI with 3D model  
- Implement realtime slicing on BeagleBone so an STL file can be sent directly (very cool).  

Known issues:  
There seems to be a bug with the software that causes the 
filament to retract after a few layers. Find out if this is consistent. 

