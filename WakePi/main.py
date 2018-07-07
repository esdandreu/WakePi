#!/usr/bin/env python3
from __future__ import unicode_literals

__version__ = '1.6'
__author__ = 'Andreu Gimenez Bolinches'

import sys
import os
import time
import telepot
import datetime
import threading
import subprocess
import traceback
from telepot.loop import MessageLoop
from commandprocess import CommandProcess
from mopidycontrols import MopidyControls
from calendarcheck import CalendarCheck
from alarmcontrols import AlarmControls
from state import State
from configcontrols import ConfigControls

BOOT_INITIALIZATION = False # Activate this for final release to get mopidy
                            # initialized again if something fails

def on_chat_message(msg):
    '''Executed when receiven a message'''
    content_type, chat_type, chat_id = telepot.glance(msg)
    print('INFO:',content_type,chat_type,chat_id)
    command = msg['text']
    is_valid = state.chat_ids(chat_id,command)
    if is_valid:
        cp.command_process(command)

def on_callback_query(msg):
    '''Executed when pressing a Telegram button'''
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('INFO: Callback Query:', query_id, from_id, query_data)
    command = query_data
    cp.command_process(command)
    #bot.answerCallbackQuery(query_id, text='Got it')

def time_check(state):
    '''Loop checking time periodically'''
    print('INFO: '+datetime.datetime.utcnow().strftime('%c'))
    last_calendar_check = datetime.datetime.utcnow()
    PERIOD_CALENDAR_CHECK = 5*60 # [seconds]
    last_refresh_token_check = datetime.datetime.utcnow()
    PERIOD_REFRESH_TOKEN_CHECK = 2*60 # [seconds]
    last_alarm_check = datetime.datetime.utcnow()
    PERIOD_ALARM_CHECK = 10 # [seconds]
    last_ringing_check = datetime.datetime.utcnow()
    PERIOD_RINGING_CHECK = 2 # [seconds]
    ringing_time = 0
    while True:
        try:
            time.sleep(1)
            now = datetime.datetime.utcnow()
            if (now-last_calendar_check).total_seconds() > PERIOD_CALENDAR_CHECK:
                last_calendar_check = now
                state.send_chat_action('typing')
                state.week_events = cal_check.get_week_events_local_times()
                state.send_chat_action('typing')
                alarm.set_auto_alarms(state.week_events)
            if (now-last_refresh_token_check).total_seconds() > PERIOD_REFRESH_TOKEN_CHECK:
                last_refresh_token_check = now
                mopidy.refresh_token()
            if not 'ringing' in state():
                if (now-last_alarm_check).total_seconds() > PERIOD_ALARM_CHECK:
                    last_alarm_check = now
                    alarm.alarm_check()
                    ringing_time = 0
            else:
                if (now-last_ringing_check).total_seconds() > PERIOD_RINGING_CHECK:
                    last_ringing_check = now
                    alarm.set_ring_volume(ringing_time)
                    ringing_time += PERIOD_RINGING_CHECK
                    if ringing_time % alarm.c.ring_refresh_sec == 0:
                        state.set_reply_text('Type:'+alarm.c.alarm_stop_password,
                                             dash_join=False)
                        state.refresh_dashboard()
                    elif ringing_time > int(alarm.c.max_ringing_time)*60:
                        state('music')
                        state.keyboard_type = 'home home'
                        mopidy.set_volume_sys(state.default_volume)
                        mopidy.clear()
                        state.auto_refresh = True
                        state.refresh_dashboard()
        except Exception as error:
            print('ERROR: time check error')
            traceback.print_tb(error.__traceback__)
            print(error)

def get_bot_token():
    '''Returns the bot token from the config file'''
    token = config.get_section('Bot Token')
    if len(token) > 1:
        print('WARNING: Only first bot token is accepted')
    return token[0]

def init_mopidy():
    ''' This code runs in loop mode if boot initialization is enabled
        It basically initalizes mopidy and waits untill is initialized
        if something happens with the network and mopidy gets an error
        it will initialize it again in a second
        '''
    state.send_chat_action('upload_audio')
    for x in range(1,4):
        time.sleep(0.5)
        try:
            subprocess.check_output(['sudo','pkill','mopidy'])
        except subprocess.CalledProcessError as e:
            print('ERROR: error killing')
    subprocess.check_output(['mopidy']) # while mopidy is active this blocks code
    print('INFO: mopidy reboot')

'''Initialization process'''
print('INFO: Start initialization')
config = ConfigControls()
bot = telepot.Bot(get_bot_token())
state = State(bot)
cp = CommandProcess(state,bot)
mopidy = MopidyControls(state)
print('INFO: spotipy version '+mopidy.spotipy_VERSION)
cal_check = CalendarCheck(state)
alarm = AlarmControls(state)
MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}
            ).run_as_thread()
#self.week_events = self.cal_check.get_week_events_local_times()
#alarm.set_auto_alarms(state.week_events)
'''Parallel process'''
if __name__ == "__main__":
    try:
        refreshParallel = threading.Thread(target = state.auto_refresh_dashboard)
        refreshParallel.setDaemon(True)
        refreshParallel.start()
        timeCheckParallel = threading.Thread(target = time_check,
                                             args = (state,))
        timeCheckParallel.setDaemon(True)
        timeCheckParallel.start()
        if BOOT_INITIALIZATION:
            initMopidy = threading.Thread(target = init_mopidy)
            initMopidy.setDaemon(True)
            initMopidy.start()
        print('\nINFO: Initialization completed\n')
    except:
        print('ERROR: unable to start thread')

# Necessary for release version with reboot mode
while True:
    pass
        
        
