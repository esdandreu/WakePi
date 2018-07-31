#!/bin/bash
sudo killall python3
sudo killall python
lxterminal --command "/home/pi/WakePi/main.py" &
exit 0
