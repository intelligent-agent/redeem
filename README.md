    :::python
                                                                     
        _/_/_/                    _/                                     
       _/    _/    _/_/      _/_/_/    _/_/      _/_/    _/_/_/  _/_/    
      _/_/_/    _/_/_/_/  _/    _/  _/_/_/_/  _/_/_/_/  _/    _/    _/   
     _/    _/  _/        _/    _/  _/        _/        _/    _/    _/    
    _/    _/    _/_/_/    _/_/_/    _/_/_/    _/_/_/  _/    _/    _/     


Redeem is the Replicape Daemon that accepts G-codes and turns them into coordinates on 
your 3D-printer. It's similar to Marlin and Teacup, only it's taylor made for Replicape and it's written in Python. 

Software features:  
- Accelleration with corner speed prediction.  
- Printer settings loaded from file  
- Controllable via ethernet, USB, printer display.   

TODO for software:  
- Better axis max-speed. It now limits the feed rate, but should instead take into account the speed in a given direction.  
- PID autotune.  
- Constant jerk?  

Known issues:  
- USB hugs all CPU, disabled for now. Use ethernet (over USB) instead.  

Wiki: http://wiki.thing-printer.com/index.php?title=Redeem
