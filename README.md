# WakePi

Raspberry Pi alarm clock that you can connect to your calendar to wake you up before your first day event with the spotify music you select, all the user interface is done with a telegram bot. Must have spotify premium, also works as a music box and spotify playing device, can reproduce youtube songs.

## Why?

I made this because I was tired of usless alarm clocks with radio that did not adapt completely to my needs. I have an irregular shedule so I can't set the same alarms every week but I have a calendar with my events, I was also tired of checking every night the tomorrow's alarm so I sincronize the alarm clock with the calendar and set the alarms automatically. I like to wake up with music so I connected it to spotify and coded a growing ring volume with time so you wake up more naturally, this volume curve and limits are totally configurable by users without needing to know how to read the code, it's all in the telegram bot UI. Why telegram as user interface? because I don't want to code a complete app, this should be simple so a simple chat is enough to set all things and you don't have to trust your phones to my android coding abilities (another reason to make it with telegram is to be multiplatform without coding twice). There is space for a lot of hacks and improvements, I wish documentation were better (That is a huge improvement space) but I hope the code is readable enough (the command process part is not the best, I know)

## Getting Started

I would love to have a file that installs everything. First of all, I install most of the things twice, as superuser and as normal user, the normal user installation is for developer debugg, the superuser installation will run at raspberry pi's boot (when it turns on the WakePi code runs too, you only need to have a screen, keyboard and mouse the first time you run it to configure a couple of things)

### Prerequisites

### Installing

## Authors

* **Andreu Giménez Bolinches** - *Initiall work* - [esdandreu](https://github.com/esdandreu)

## License

This project is licensed under the GNUv3 license - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments
