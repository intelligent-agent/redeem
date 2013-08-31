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
-   Open source hard ware and software.  
-   Software written in Python for maintainability and hackability.  
  
TODO for software:  
- Optimize the merging of timings from the different steppers.  
- Make a fancy GUI with 3D model  
- Implement realtime slicing on BeagleBone so an STL file can be sent directly (very cool).  
- Printer settings loaded from file

Known issues:  
The print stops right at the last command. Somethimes this also happens initially, but 
has not ben seen during prints. 

Blog: http://hipstercircuits.com  
Wiki: wiki.replicape.com
