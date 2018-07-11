from __future__ import unicode_literals

from time import sleep
import subprocess
import telepot
import datetime
from telepot.namedtuple import (InlineKeyboardMarkup, InlineKeyboardButton,
                                ReplyKeyboardMarkup, KeyboardButton,
                                ReplyKeyboardRemove)
from mopidycontrols import MopidyControls
from alarmcontrols import AlarmControls
from calendarcheck import CalendarCheck
from asciifont import AsciiFont
from configcontrols import ConfigControls
from collections import namedtuple

class State( object ):
    def __init__(self, bot):
        '''Config'''
        self.max_msg_line_length = 29
        self.max_reply_line_length = 28
        '''Initializations'''
        self.config = ConfigControls()
        self.mopidy = MopidyControls(self)
        self.mopidy.refresh_token()
        self.alarm = AlarmControls(self)
        self.cal_check = CalendarCheck(self)
        self.font = AsciiFont()
        self.bot = bot
        self.default_volume = self.get_default_control("volume")
        self.mopidy.set_volume_sys(self.default_volume)
        self.set_reply_text('')
        '''General variables'''
        self.state = 'music'
        self.dashboard_type = 'music'
        self.keyboard_type = 'home home'
        self.music_status = self.mopidy.get_status()
        self.last_dash_msg = [False]
        self.last_reply_msg = [False]
        self.chat_id_list = []
        self.chat_password = self.get_password()
        self.auto_refresh_enabled = True
        self.week_events = [[],[],[],[],[],[],[]]
        self.set_alarm_day = 0
        self.snooze_counts = 0
        self.set_config_name = ' '
        self.alarm_to_edit = [['manual','disabled'],datetime.time(hour=0,minute=0)]
        '''Search stored variables'''
        self.search_type = False
        self.search_query = False
        self.options_list = False
        self.uri_list = False
        self.uri = False
        
    def __call__(self,state=None):
        if state is None:
            return self.state
        else:
            self.state = state
            print('INFO: state changed to', state)
    
    def get_password(self):
        '''Returns the password from the config file'''
        password = self.config.get_section('Password')
        if len(password) > 1:
            print('WARNING: Only first chat password is accepted')
        return password[0].strip(' ')

    def get_default_control(self,control):
        '''Returns the desired default control from the config file'''
        text = self.config.get_section('Default Controls')
        for line in text:
            if control in line:
                default_control = line.split(" = ")[1]
                if default_control.isdigit():
                    default_control = int(default_control)
                return default_control
        return False

    def set_default_control(self,control,value):
        '''Changesthe desired default control in the config file'''
        text = self.config.get_section('Default Controls')
        new_text = []
        for line in text:
            if control in line:
                new_text.append(control+' = '+str(value))
            else:
                new_text.append(line)
        self.config.set_section('Default Controls',new_text)
        return True
            
    def dashboard(self):
        '''Selects a dashboard to output'''
        dashboard_type = self.dashboard_type
        if  'music' in dashboard_type:
            status = self.music_status
            if status.random:
                random_indicator = u'\U00002714 \U0001F500'
            else:
                random_indicator = u'\U0000274C \U0001F500'
            if status.repeat:
                repeat_indicator = u'\U00002714 \U0001F501'
            else:
                repeat_indicator = u'\U0000274C \U0001F501'
            if status.playing:
                play_indicator = u'\U000023F8'
            else:
                play_indicator = u'\U000025B6'
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                           [InlineKeyboardButton(text=u'\U000023EE', callback_data='/prev'),
                            InlineKeyboardButton(text=play_indicator, callback_data='/play'),
                            InlineKeyboardButton(text=u'\U000023ED', callback_data='/next')],
                           [InlineKeyboardButton(text=u'\U000023EA', callback_data='/step_prev'),
                            InlineKeyboardButton(text=u'\U000023F9', callback_data='/stop'),
                            InlineKeyboardButton(text=u'\U000023E9', callback_data='/step_next')],
                           [InlineKeyboardButton(text=random_indicator, callback_data='/random_mode'),
                            InlineKeyboardButton(text=u'\U0001F508 \U0001F53B', callback_data='/volume_down'),
                            InlineKeyboardButton(text=u'\U0001F50A \U0001F53A', callback_data='/volume_up'),
                            InlineKeyboardButton(text=repeat_indicator, callback_data='/repeat_mode')],
                       ])
        elif 'ring' in dashboard_type:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                           [InlineKeyboardButton(text=u'\U0001F634'+'/snooze'+u'\U0001F634', callback_data='/snooze')],
                       ])
        elif 'snooze' in dashboard_type:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                           [InlineKeyboardButton(text='refresh time counter', callback_data='/time')],
                       ])
        elif 'alarm view' in dashboard_type:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                           [InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:0'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:1'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:2'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:3'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:4'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:5'),
                            InlineKeyboardButton(text=u'\U0001F527', callback_data='/set_alarm:6'),
                            InlineKeyboardButton(text=u'\U00002699', callback_data='/change_config'),
                            ],
                       ])
        elif 'alarm config' in dashboard_type:
            inline_keyboard_array = []
            config_list = self.alarm.get_config()
            for name in config_list._fields:
                if not 'ring_music' in name:
                    value = getattr(config_list,name)
                    units = self.alarm.get_config_units(name)
                    if isinstance(value,int):
                        value = str(value)
                    button_text = u'\U00002699' + name + ' = ' + value + units 
                    inline_keyboard_array.append([InlineKeyboardButton(
                        text=button_text, callback_data=name)])
            keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard_array)
        elif 'general_config' in dashboard_type:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Password', callback_data='set_password')],
                [InlineKeyboardButton(text='Add calendar', callback_data='add_calendard')],
                [InlineKeyboardButton(text='Remove calendar', callback_data='remove_calendar')],
                [InlineKeyboardButton(text='Default Volume = '+str(self.default_volume), callback_data='default_volume')],
                ])                          
        else:
            keyboard = False
        return keyboard

    def keyboard(self):
        '''Selects a reply keyboard to output'''
        keyboard_type = self.keyboard_type
        if  'home home' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text='menu')],
                           ],
                            resize_keyboard = True,
                            #on_time_keyboard = True, (not supported by current telepot version)
                       )
        elif 'home menu' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U000023EF'+'music')],
                           [KeyboardButton(text=u'\U000023F0'+'alarm')],
                           [KeyboardButton(text=u'\U0001F529'+'configuration')],
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'music' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0001F3A7 \U0001F4DD'+'playlists')],
                           [KeyboardButton(text=u'\U0001F50E'+'search')],
                           [KeyboardButton(text=u'\U0001F534'+'youtube help')],
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'search type' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0000270F \U0001F3B5'+'track')],
                           [KeyboardButton(text=u'\U0001F919 \U0001F399'+'artist')],
                           [KeyboardButton(text=u'\U0001F3B6 \U0001F4BF'+'album')],
                           [KeyboardButton(text=u'\U0001F3A7 \U0001F4DD'+'playlist')],
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'options list' in keyboard_type:
            if self.options_list:
                keyboard_buttons_list = []
                for option in self.options_list:
                    keyboard_buttons_list.append(
                        [KeyboardButton(text=option)] )
                keyboard_buttons_list.append([KeyboardButton(text=u'\U0001F519'+'/return')])
                keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons_list,
                                               resize_keyboard = False,
                                               )
            else:
                print('WARNING: options_list is empty')
                keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,)
        elif 'action' in keyboard_type:
            if self.uri:
                action_list = [u'\U000023E9'+'play',u'\U000023CF'+'add']
                if ('artist' in self.uri or 'playlist' in self.uri
                    or 'album' in self.uri):
                    action_list.append(u'\U0001F500'+'shuffle')
                    action_list.append(u'\U0000270F \U0001F3B5'+'tracks')
                if 'artist' in self.uri:
                    action_list.append(u'\U0001F3B6 \U0001F4BF'+'albums')
                if 'playlist' in self.uri:
                    action_list.append(u'\U0001F634'+'wake up music'+u'\U0001F918')
                keyboard_buttons_list = []
                for option in action_list:
                    keyboard_buttons_list.append(
                        [KeyboardButton(text=option)] )
                keyboard_buttons_list.append([KeyboardButton(text=u'\U0001F519'+'/return')])
                keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons_list,
                                               resize_keyboard = False,
                                               )
            else:
                keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,)
        elif 'alarm menu' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U000023F1'+'set_alarm')],
                           [KeyboardButton(text=u'\U000023F3'+'temporizer')],
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'alarm set on_day' in keyboard_type:
            keyboard_buttons_list = []
            for event in self.week_events[self.set_alarm_day]:
                event = (event -
                    datetime.timedelta(minutes=int(self.alarm.c.other_event_time_before)))
                keyboard_buttons_list.append(
                    [KeyboardButton(text=event.strftime(
                        'set '+u'\U0001F5D3'+u'\U0001F519'+"-%H:%M"))] )
            week_alarms = self.alarm.get_week_alarms_localtime()
            _type=0
            _time=1
            for alarm_info in week_alarms[self.set_alarm_day]:
                if 'auto' in alarm_info[_type][0]:
                    a_type0 = u'\U0001F3E7 '
                else:
                    a_type0 = u'\U000024C2 '
                if 'disabled' in alarm_info[_type][1]:
                    a_type1 = u'\U0001F4F4 '
                else:
                    a_type1 = u'\U0001F51B '
                keyboard_buttons_list.append(
                    [KeyboardButton(text=alarm_info[_time].strftime(
                        "edit "+a_type0+a_type1+u'\U000023F0'+"-%H:%M"))] )
            keyboard_buttons_list.append([KeyboardButton(
                text=u'\U000023F1'+'add new'+u'\U0001F195')])
            keyboard_buttons_list.append([KeyboardButton(text=u'\U0001F519'+'/return')])
            keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons_list,
                                               resize_keyboard = False,
                                               )
        elif 'alarm edit' in keyboard_type:
            if 'enabled' in self.alarm_to_edit[0][1]:
                toggle_text = u'\U0001F4F4'+'disable'
            else:
                toggle_text = u'\U0001F51B'+'enable'
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=toggle_text)],
                           [KeyboardButton(text=u'\U0001F527'+'change')],
                           [KeyboardButton(text=u'\U00002620'+'delete')],
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'ringing' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0001F634'+'/snooze'+u'\U0001F634')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'return' in keyboard_type:
            keyboard = ReplyKeyboardMarkup(keyboard=[
                           [KeyboardButton(text=u'\U0001F519'+'/return')],
                           ],
                            resize_keyboard = True,
                       )
        elif 'nothing' in keyboard_type:
            keyboard = ReplyKeyboardRemove(remove_keyboard=True)
        else:
            keyboard = False
        return keyboard

    def refresh_dashboard(self):
        '''Deletes last message and sends a new one'''
        msg_text = self.get_msg_text()
        tries = 0
        chat_count = 0
        for chat_id in self.chat_id_list:
            '''Sends the message with dashboard and the message with custom keyboard
               to every allowed chat id
               '''
            while tries < 2:
                try:
                    dashboard = self.dashboard()
                    keyboard  = self.keyboard()
                    dash_msg_id = self.bot.sendMessage(chat_id, msg_text,
                                                       parse_mode = 'Markdown',
                                                       reply_markup = dashboard
                                                       )
                    reply_msg_id = self.bot.sendMessage(chat_id, self.reply_text,
                                                        parse_mode = 'Markdown',
                                                        reply_markup = keyboard
                                                        )
                    self.delete_last_msg(self.bot,chat_count)
                    self.set_reply_text('')
                    self.store_dash_msg(chat_count,telepot.message_identifier(dash_msg_id))
                    self.store_reply_msg(chat_count,telepot.message_identifier(reply_msg_id))
                    print('INFO: Refresh')
                    break
                except Exception as error:
                    tries = tries + 1
                    print('ERROR: could not refresh')
                    print(error)
            chat_count += 1
        return
    
    def get_msg_text(self):
        if 'music' in self.state:
            self.music_status = self.mopidy.get_status()
            status = self.music_status
            if status.playing:
                playing_indicator = u'\U0001F918'
            else:
                playing_indicator = u'\U0000270B'
            if len(status.song) > self.max_msg_line_length:
                status.song = ''.join([status.song[:self.max_msg_line_length-3], '...'])
            if len(status.artist) > self.max_msg_line_length:
                status.artist = ''.join([status.artist[:self.max_msg_line_length-2], '...'])
            msg_text = ''.join(
                    ['`' + (self.max_msg_line_length-2)*'-' + '`' + '\n',
                    playing_indicator,'*',status.song,'*',playing_indicator,'\n',
                    u'\U0001F3A4','_',status.artist,'_',u'\U0001F3B8','\n',
                    u'\U0001F3B6','`',status.song_number,'` ',
                    u'\U000023F3','_',status.song_time,'_ ',
                    u'\U0001F509','`',status.volume,'`'])
            self.dashboard_type = 'music'
        elif 'alarm' in self.state:
            if 'change_config' in self.state:
                text = 'Alarm Configuration'
                msg_text = ('`' + int((self.max_reply_line_length
                                - len(text))/2)*'-' + text
                                + int((self.max_reply_line_length +1
                                - len(text))/2)*'-' + '`')
                self.dashboard_type = 'alarm config'
            else:
                msg_text = self.alarm.build_msg_text_from_alarms()
                self.dashboard_type = 'alarm view'
        elif 'ringing' in self.state:
            now = self.alarm.to_localtime(datetime.datetime.utcnow())
            hour = now.strftime("%H")
            minu = now.strftime("%M")
            msg_list =[]
            hour0 = self.font(int(hour[0]))
            hour1 = self.font(int(hour[1]))
            for index in range(0,len(hour0)):
                msg_list.append('`'+'  '+hour0[index]+' '+hour1[index]+'`')
            msg_list.append(' ')
            minu0 = self.font(int(minu[0]))
            minu1 = self.font(int(minu[1]))
            point = ['  ','  ','# ','  ','# ','  ','  ']
            for index in range(0,len(minu0)):
                msg_list.append('`'+point[index]+minu0[index]+' '+minu1[index]+'`')
            msg_text='\n'.join(msg_list)
            self.dashboard_type = 'ring'
        elif 'snooze' in self.state:
            t = self.alarm.alarm_check()
            seconds = str(int(t%60))
            if len(seconds)<2:
                seconds = '0'+seconds
            minutes = str(int(t/60)%60)
            if len(minutes)<2:
                minutes = '0'+minutes
            msg_text =  (u'\U0001F634'+u'\U0001F634'+u'\U000023F3'+u'\U000027A1'
                        +'` `'+minutes[0]+u'\U000020E3'+minutes[1]+u'\U000020E3'
                        +'*:*'+seconds[0]+u'\U000020E3'+seconds[1]+u'\U000020E3'
                        +u'\U0001F634'+u'\U0001F634')
            self.dashboard_type = 'snooze'
        elif 'general_config' in self.state:
            text = 'General Configuration'
            msg_text = ('`' + int((self.max_reply_line_length
                            - len(text))/2)*'-' + text
                            + int((self.max_reply_line_length +1
                            - len(text))/2)*'-' + '`')
            self.dashboard_type = 'general_config'
        else:
            msg_text = '***WIP***'
            self.dashboard_type = ' '
        return msg_text
    
    def set_reply_text(self,text=None,dash_join=True):
        if text is None:
            return self.reply_text
        else:
            if dash_join:
                text = '-'.join(text.strip(' ').split(' '))
            else:
                text = ' '.join(text.strip(' ').split(' '))
            self.reply_text = ('`' + int((self.max_reply_line_length
                                   - len(text))/2)*'-' + text
                                   + int((self.max_reply_line_length +1
                                   - len(text))/2)*'-' + '`')

    def send_chat_action(self,action):
        '''Valid actions: upload_audio, typing
           '''
        for chat_id in self.chat_id_list:
            self.bot.sendChatAction(chat_id,action)
      
    def auto_refresh_dashboard(self):
        ''' Process performed in parallel with the 'mpc idle' command
            that waits until something changes in the music player
            '''
        while True:
            try:
                subprocess.check_output(['mpc','idle'])
                if self.auto_refresh_enabled:
                    print('INFO: auto')
                    self.refresh_dashboard()
                else:
                    print('INFO: auto not enabled')
            except Exception as error:
                print('WARNING: Mopidy not enabled')
                print(error)
                self.send_chat_action('upload_audio')
                sleep(2)# HUGE BLOCK
        

    def auto_refresh(self,enabled=None):
        '''Enables or disables auto refresh process'''
        if enabled is None:
            return self.auto_refresh_enabled
        else:
            self.auto_refresh_enabled = enabled
        
    def chat_ids(self,new_chat_id=None,command=None):
        '''Returns the chat ids allowed or adds a new chat id allowed
           if the password given is correct
           '''
        if new_chat_id is None:
            return self.chat_id_list
        else:
            is_new = True
            for chat_id in self.chat_id_list:
                if new_chat_id == chat_id:
                    if command is not None:
                        if '/exit' in command:
                            self.chat_id_list.remove(new_chat_id)
                            self.bot.sendMessage(new_chat_id,
                                                 'Goodbye')
                            print('INFO: Allowed chat ids:')
                            print(self.chat_id_list)
                            return False
                        else:
                            is_new = False
                    else:
                        is_new = False
            if is_new:
                if self.chat_password in command:
                    self.chat_id_list.append(new_chat_id)
                    print('INFO: Allowed chat ids:')
                    print(self.chat_id_list)
                    self.set_reply_text('Welcome')
                    self.refresh_dashboard()
                else:
                    self.bot.sendMessage(new_chat_id,
                                         'Type correct password')
                return False
            else:
                return True
         
    def store_dash_msg(self,chat_count,msg=None):
        '''Returns and stores the last message id to
           delete the message afterwards
           '''
        if len(self.last_dash_msg)>chat_count:
            if msg is None:
                return self.last_dash_msg[chat_count]
            else:
                self.last_dash_msg[chat_count] = msg
        elif len(self.last_dash_msg)==chat_count:
            if msg is None:
                return False
            else:
                self.last_dash_msg.append(msg)
        else:
            print('ERROR: store last msg')
            return False

    def store_reply_msg(self,chat_count,msg=None):
        '''Returns and stores the last message id to
           delete the message afterwards
           '''
        if len(self.last_reply_msg)>chat_count:
            if msg is None:
                return self.last_reply_msg[chat_count]
            else:
                self.last_reply_msg[chat_count] = msg
        elif len(self.last_reply_msg)==chat_count:
            if msg is None:
                return False
            else:
                self.last_reply_msg.append(msg)
        else:
            print('ERROR: store last msg')
            return False
                
    def delete_last_msg(self,bot,chat_count):
        '''Deletes last message sent'''
        try:
            bot.deleteMessage(self.last_dash_msg[chat_count])
            bot.deleteMessage(self.last_reply_msg[chat_count])
        except Exception:
            print('WARNING: First msg?')
