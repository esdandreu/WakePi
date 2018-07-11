# WakePi

Raspberry Pi alarm clock that you can connect to your calendar to wake you up before your first day event with the spotify music you select, all the user interface is done with a telegram bot. Must have spotify premium, also works as a music box and spotify playing device, can reproduce youtube songs.

## Why?

I made this because I was tired of usless alarm clocks with radio that did not adapt completely to my needs. I have an irregular shedule so I can't set the same alarms every week but I have a calendar with my events, I was also tired of checking every night the tomorrow's alarm so I sincronize the alarm clock with the calendar and set the alarms automatically. I like to wake up with music so I connected it to spotify and coded a growing ring volume with time so you wake up more naturally, this volume curve and limits are totally configurable by users without needing to know how to read the code, it's all in the telegram bot UI. Why telegram as user interface? because I don't want to code a complete app, this should be simple so a simple chat is enough to set all things and you don't have to trust your phones to my android coding abilities (another reason to make it with telegram is to be multiplatform without coding twice). There is space for a lot of hacks and improvements, I wish documentation were better (That is a huge improvement space) but I hope the code is readable enough (the command process part is not the best, I know)

## **Getting Started**

First of all, all this code has been tested in a RPi 3B, I assume that your RPi is connected to the Internet by means of cable or wifi.

I would love to have a file that installs everything. I install some things twice, as superuser and as normal user, the normal user installation is for developer debugg, the superuser installation will run at raspberry pi's boot (when RPi turns on the WakePi code runs too, you only need to have a screen, keyboard and mouse the first time you run it to configure a couple of things)

## Prerequisites

### Have a Raspberry Pi with Raspbian
I can't buy you a RPi but I can show you [how to install Raspbian](https://www.raspberrypi.org/documentation/installation/noobs.md)

### Have a Telegram bot (UI)
[Create a telegram bot using a telegram bot, BotFather](https://core.telegram.org/bots#6-botfather)

Get your Bot Token and have it ready to put in your "config.txt" file on the Raspberry Pi, it has to look like this:
```
[Bot Token]
4--------------Your bot token--------------jA
```
### Have Mopidy installed as a service

#### *Install mopidy*

[Install mopidy in a raspberry pi](https://docs.mopidy.com/en/latest/installation/raspberrypi/)

[Run the following commands in terminal](https://docs.mopidy.com/en/latest/installation/debian/#debian-install)
```
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/stretch.list
sudo apt-get update
sudo apt-get install mopidy
```

#### *Install mpd*

Run in terminal:
```
sudo apt-get install mpd
```

#### *Install spotify and youtube extensions*

[Spotify](https://github.com/mopidy/mopidy-spotify)
```
sudo apt-get install mopidy-spotify
```
[Spotify tuningo](https://github.com/trygveaa/mopidy-spotify-tunigo)
```
sudo apt-get install mopidy-spotify-tuningo
```
[Youtube](https://github.com/mopidy/mopidy-youtube)
```
sudo apt-get install mopidy-youtube
```

#### *Configure it as a service*

[Running as a service on Debian/Raspbian](https://docs.mopidy.com/en/latest/service/#service-management-on-debian)
```
sudo dpkg-reconfigure mopidy
```

### Install Raspotify
[Github](https://github.com/dtcooper/raspotify)

```
curl -sL https://dtcooper.github.io/raspotify/install.sh | sh
```
If you want to change the device name that will appear in the spotify devices window run in terminal:
```
sudo nano /etc/default/raspotify
```
Go to where "device name" is written, erase the comment character "#" and write the device name that you want.
To save the changes and exit press "Ctrl+X", then "Y" and "Enter".

### Install dependencies
Run the following commands in terminal
```
sudo pip2 install youtube-dl
sudo pip3 install icalendar
sudo pip3 install telepot
sudo pip3 install subprocess
sudo pip3 install spotipy
```
(If you want to develope and test things in the python console you will need to install again the dependencies without "sudo", that is for superusers that is the way python is run at boot)

## Installing WakePi

### Clone the folder

```
git clone git://github.com/esdandreu/WakePi.git
```

### Replace Files
First give access to the files, run in terminal:
```
sudo chmod 777 .local/lib/python3.5/site-packages/spotipy/client.py
sudo chmod 777 usr/local/lib/python3.5/dist-packages/spotipy/client.py
sudo chmod 777 /home/pi/.config/mopidy/etc/mopidy/mopidy.conf
```
Copy files from "Files to replace" in the corresponding directories, that is:
client.py -> .local/lib/python3.5/site-packages/spotipy/client.py
client.py -> usr/local/lib/python3.5/dist-packages/spotipy/client.py
mopidy.conf -> /home/pi/.config/mopidy/etc/mopidy/mopidy.conf

(Why change client.py? [Because the pip installation of spotify is outdated](https://stackoverflow.com/questions/47028093/attributeerror-spotify-object-has-no-attribute-current-user-saved-tracks)

Why change mopidy.conf? Because I give you a preconfigured file that will save work.)

### Configure your spotify account

First input your username and password in the mopidy.conf section of Spotify, run in terminal:
```
sudo nano /home/pi/.config/mopidy/etc/mopidy/mopidy.conf
```
Go to the bottom of the file and put your credentials in the username and password
```
[spotify]
enabled = true
username = *Your username*
password = *Your password*
client_id = e31f747ffb9f434ab466792e6c7f5a6a
client_secret = 65704cb4f9e841e7b2601882ced44e89
```
To save the changes and exit press "Ctrl+X", then "Y" and "Enter".
You need a premium account. If you are logged with facebook check this: [username](https://www.spotify.com/account/overview/) [password](https://www.spotify.com/au/account/set-device-password/)
I give you the client_id and the client_secret of my Spotify app, if you prefer to create your you can do it [here](https://developer.spotify.com/my-applications/#!/applications)

**Then go to the config.txt located in the WakePi folder and add there the username too.**
You don't need to add the password there but the first time you run the code you will be prompt to log in your spotify account and grant access to the app, then you have to copy the full url of the webpage you have been redirected (google) and paste it in the terminal ("Ctrl+Mayus+V")

### Enable auto boot

[Where I get the info](https://www.wikihow.com/Execute-a-Script-at-Startup-on-the-Raspberry-Pi)
First give access to the file, run in terminal:
```
chmod +x /home/pi/WakePi/main.py
```
Then open the autostart file, run in terminal:
```
sudo nano /home/pi/.config/lxsession/LXDE-pi/autostart
```
After this line:
```
@pcmanfm --desktop --profile LXDE-pi
```
You have to write this:
```
@sudo /home/pi/WakePi/init_wakepi.sh
```
And that's all folks! Reboot the RPi and check that everything works correctly.

### Sync with google calendar (or other ical calendars)

In the telegram UI (bot), once you send the password and press "menu" you will see a configuration opion, there you can add calendars in a url ical format. [How to get that url from google calendar](https://mas.echurchgiving.com/hc/en-us/articles/115004079647-How-do-I-get-an-iCal-feed-from-Google-Calendar-)

## Authors

* **Andreu Giménez Bolinches** - *Initiall work* - [esdandreu](https://github.com/esdandreu) - [Donations allowed](https://www.paypal.me/esdandreu)

## License

This project is licensed under the GNUv3 license - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

First of all to the [mopidy team](https://www.mopidy.com/)

To the [Raspotify](https://github.com/dtcooper/raspotify) creator that allows the raspberry pi to be used as a spotify device.

And to the creators of all the other dependecies I use.
