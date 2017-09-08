Webcam
======

Webcam streaming has been tested with Logitech C270. Most of this is
from:
https://github.com/foosel/OctoPrint/wiki/Setup-on-BeagleBone-Black-running-%C3%85ngstr%C3%B6m#webcam

mjpg-streamer is shipped with Umikaze 2.1 by default. It is on and if
you have a webcam plugged in before powering up, the streams should
return video if your webcam is supported.

The stream should be available through
`http://kamikaze.local:8080/?action=stream
http://kamikaze.local:8080/?action=stream <http://kamikaze.local:8080/?action=stream_http://kamikaze.local:8080/?action=stream>`__
To integrate this in Octoprint:

`` nano /home/octo/.octoprint/config.yaml``

Add this to the webcam section if octoprint isn't showing the feed
already:

| `` webcam:``
| ``   stream: ``\ ```http://kamikaze.local:8080/?action=stream`` <http://kamikaze.local:8080/?action=stream>`__
| ``   snapshot: ``\ ```http://kamikaze.local:8080/?action=snapshot`` <http://kamikaze.local:8080/?action=snapshot>`__
| ``   ffmpeg: /usr/bin/ffmpeg``

Restart octoprint