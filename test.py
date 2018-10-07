from __future__ import absolute_import, print_function, unicode_literals

import telepot
from telepot.namedtuple import (InlineKeyboardMarkup, InlineKeyboardButton,
                                ReplyKeyboardMarkup, KeyboardButton,
                                ReplyKeyboardRemove)
import datetime
import numpy
from mopidycontrols import MopidyControls
from calendarcheck import CalendarCheck
from alarmcontrols import AlarmControls
from asciifont import AsciiFont
from configcontrols import ConfigControls
from state import State
config = ConfigControls()
#playlists = mopidy.list_playlist()

bot = telepot.Bot('480048418:AAG0MQtEDw2FXImhbMv9pv4zBAfjK2ZbGjA')
state = State(bot)
self = state
mopidy = MopidyControls(state)
chat_id = 463574550
alarm = AlarmControls(state)
font = AsciiFont()
cal_check = CalendarCheck()
state.chat_id_list.append(chat_id)
state.keyboard_type = 'alarm set on_day'
state('alarm view')


#alarm.set_config('max_ringing_volume','60')

#state.refresh_dashboard()
##msg_text = state.get_msg_text()
##dashboard = InlineKeyboardMarkup(inline_keyboard=[
##                           [InlineKeyboardButton(text=u'\U0001F527', callback_data='1'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='2'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='3'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='4'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='5'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='6'),
##                            InlineKeyboardButton(text=u'\U0001F527', callback_data='7'),
##                            InlineKeyboardButton(text=u'\U00002699', callback_data='h'),
##                            ],
##                       ])
##dash_msg_id = bot.sendMessage(chat_id, msg_text,
##                                    parse_mode = 'Markdown',
##                                    reply_markup = dashboard
##                                                       )


#today = datetime.datetime.utcnow().date()


#mopidy.load('spotify:user:2155eprgg73n7x46ybpzpycra:playlist:64xSAgfPBl8HjIKJBi3CIi','uri')

#mopidy.clear()
##status_full = mopidy.status()
##print(status_full)
#mopidy.load("Go hard or go home",'playlist')
#mopidy.load('spotify:track:02dphTJYUQ9pmdNC52iyOz','uri')
#mopidy.play()

#output = mopidy.spotify.search(q='mago',limit=2,type='album')
#[slist,ulist] = mopidy.search_spotify('mago de oz','artist')
#utcoffset = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)
