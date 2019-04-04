Endstops
========

..  raw:: html

    <iframe width="560" height="315" src="https://www.youtube.com/embed/5LEjdQtIYe4" frameborder="0" allowfullscreen></iframe>

This was a short troubleshooting advice provided on Slack - it's being
pasted here as-is until it can be rephrased and re-worked into the
documentation properly:

Redeem basic endstop config! First and foremost make sure your endstops
are working before trying to move. Now in redeem that is not quite as
simple as you would expect. For these instructions make sure your bed is
somewhere near the middle of its travel we do not want anything crashing
into anything!

Go to your terminal in Octoprint and press your enstops with your finger
one at a time you should get a response saying enstop # hit (# being
what axis you just triggered) If you do not get a response Stop do not
go further until you do get a resposnse!

Next go to your controls in octoprint and select 1mm and for Z press the
UP arrow it should move 1mm away from bed for some printers with fixed
beds that means usually the nozzle moves up! On others that have a bed
that moves away from the nozzle because the nozzle is fixed in the Z
plane it means the bed moves down!

We will stay with the Z axis now press the Z endstop and again try to
move 1mm UP ( UP Arrow) if it does not move try moving the Z with the
Down button it should move one or the other way this with tell you which
way you have the endstop stopping movement.

For your particular printer and endstop location you need to edit the
end\_stop\_Z1\_stops = z\_cw #stopping direction in a clockwise
direction (I think you can use pos or neg as well) end\_stop\_Z1\_stops
= z\_ccw #stopping direction in a counter clockwise

Soft Enstops You must have these set to outside your full travel in the
min and the max soft\_end\_stop\_min\_z = -0.30 #300mm set to your
printer travel plus some extra soft\_end\_stop\_max\_z = 0.30 #300mm you
can configure to suit your requirements after! these settings are in
METERS

If these are set wrong you will not move as expected you will not probe
as expected!!!!

If you need to change direction of motors this is the line 1 or -1
direction\_z = -1

The other Axis will be a similar procedure.