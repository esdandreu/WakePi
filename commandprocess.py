from __future__ import unicode_literals

import telepot
import os
import datetime
import subprocess
from alarmcontrols import AlarmControls
from mopidycontrols import MopidyControls
import sys
import logging
logger = logging.getLogger('WakePi')

class CommandProcess:
    def __init__(self, state, bot):
        self.state = state
        self.bot = bot
        self.alarm = AlarmControls(self.state)
        
    def command_process(self, command):
        ## Command processing (most hackable part)
        if '/reboot' in command:
            self.reboot()
            return
        elif '/update' in command:
            self.update()
            return
        elif '/refresh' in command:
            self.state.refresh_dashboard()
            return
            
            ''' Music player Controls'''
        if 'music' in self.state():
            end_of_command_refresh = False
            self.state.auto_refresh_enabled = True
            if '/play' in command:
                end_of_command_refresh = self.state.mopidy.toggle()
            elif '/pause' in command:
                end_of_command_refresh = self.state.mopidy.pause()
            elif '/stop' in command or '/clear' in command:
                end_of_command_refresh = self.state.mopidy.clear()
            elif '/prev' in command:
                end_of_command_refresh = self.state.mopidy.prev()
            elif '/next' in command:
                end_of_command_refresh = self.state.mopidy.next()
            elif '/step_prev' in command:
                end_of_command_refresh = self.state.mopidy.seek(-10)
            elif '/step_next' in command:
                end_of_command_refresh = self.state.mopidy.seek(+10)
            elif '/random_mode' in command:
                end_of_command_refresh = self.state.mopidy.random()
            elif '/repeat_mode' in command:
                end_of_command_refresh = self.state.mopidy.repeat()
            elif '/volume_down' in command:
                end_of_command_refresh = self.state.mopidy.volume_sys(-5)
            elif '/volume_up' in command:
                end_of_command_refresh = self.state.mopidy.volume_sys(5)
            elif '/ring' in command: #For testing purposes
                self.alarm.ring()

            else:
                end_of_command_refresh = True
                '''Substates'''
                '''Menu navigation (it's in the music display)'''
                if 'menu' in command:
                    self.state.keyboard_type = 'home menu'
                elif 'music' in command:
                    self.state.options_list = False
                    self.state.uri_list = False
                    self.state('music menu')
                    self.state.keyboard_type = 'music'
                elif 'alarm' in command:
                    self.state.options_list = False
                    self.state.uri_list = False
                    self.state('alarm view')
                    self.state.keyboard_type = 'alarm menu'
                elif 'configuration' in command:
                    self.state.options_list = False
                    self.state.uri_list = False
                    self.state('general_config view')
                    self.state.keyboard_type = 'return'
                elif 'youtu.be' in command:
                    '''If sending a link from youtube app'''
                    self.state.options_list = False
                    self.state.uri_list = False
                    video_id = command.split('/')[-1]
                    self.state.uri = ('yt:http://youtube.com/watch?v='
                                      + video_id)
                    logger.info(''+self.state.uri)
                    self.state('music search action')
                    self.state.keyboard_type = 'action'
                    self.state.set_reply_text('Youtube shared link')
                elif 'youtube.com' in command:
                    '''If sending a url'''
                    self.state.options_list = False
                    self.state.uri_list = False
                    for element in command.split(' '):
                        if 'http://' in element or 'https://' in element:
                            self.state.uri = 'yt:' + element
                    logger.info(''+self.state.uri)
                    self.state('music search action')
                    self.state.keyboard_type = 'action'
                    self.state.set_reply_text('Youtube url')
                    
                    '''Music'''
                elif 'music menu' in self.state():
                    if '/return' in command:
                        self.state('music')
                        self.state.keyboard_type = 'home menu'
                    elif 'playlists' in command:
                        [playlist_list,uri_list] = self.state.mopidy.list_playlist_spotify()
                        self.state.options_list = playlist_list
                        self.state.uri_list = uri_list
                        self.state('music search results')
                        self.state.keyboard_type = 'options list'
                    elif 'search' in command:
                        self.state('music search type')
                        self.state.keyboard_type = 'search type'
                        self.state.set_reply_text('Search by')
                    elif 'youtube help' in command:
                        end_of_command_refresh = False
                        with open('youtube_help.txt','r') as help_file:
                            help_text = help_file.read().replace('\n','')
                        for chat_id in self.state.chat_id_list:
                            self.bot.sendMessage(chat_id, help_text)
                    elif 'spotify device not found?' in command:
                        end_of_command_refresh = False
                        self.restart_raspotify()
                    else:
                        self.state.set_reply_text('Command not recognized')
                    
                elif 'music search' in self.state():
                    if 'type' in self.state():
                        if '/return' in command:
                            self.state('music menu')
                            self.state.keyboard_type = 'music'
                        else:
                            logger.info('search by', self.remove_unicode(command))
                            self.state.search_type = (self.remove_unicode(command)).strip(' ')
                            self.state('music search query')
                            self.state.keyboard_type = 'nothing'
                            self.state.set_reply_text('Search what?')
                    elif 'query' in self.state():
                        if '/return' in command:
                            self.state('music search type')
                            self.state.keyboard_type = 'search type'
                            self.state.set_reply_text('Search by')
                        else:
                            logger.info('search:', self.remove_unicode(command))
                            for chat_id in self.state.chat_id_list:
                                self.bot.sendChatAction(chat_id,'typing')
                            self.state.search_query = (self.remove_unicode(command)).strip(' ')
                            [search_list,uri_list] = self.state.mopidy.search_spotify(
                                                        self.state.search_query,
                                                        self.state.search_type)
                            self.state.search_query = False
                            self.state.search_type = False
                            if search_list and uri_list:
                                self.state.options_list = search_list
                                self.state.uri_list = uri_list
                                self.state('music search results')
                                self.state.keyboard_type = 'options list'
                                self.state.set_reply_text('Found this')
                            else:
                                self.state('music menu')
                                self.state.keyboard_type = 'music menu'
                                self.state.set_reply_text('Error')
                    elif 'results' in self.state():
                        logger.info('selection:', self.remove_unicode(command))
                        if '/return' in command:
                            if self.state.uri:
                                self.state.options_list = False
                                self.state.uri_list = False
                                self.state('music search action')
                                self.state.keyboard_type = 'action'
                                self.state.set_reply_text('What to do?')
                            else:
                                self.state('music menu')
                                self.state.keyboard_type = 'music'
                        else:
                            self.state.uri = self.selection_process(command)
                            if not self.state.uri:
                                logger.error('Selection not in the list')
                                self.state.set_reply_text('Selection not in the list')
                            else:
                                self.state('music search action')
                                self.state.keyboard_type = 'action'
                                self.state.set_reply_text('What to do?')
                    elif 'action' in self.state():
                        if '/return' in command:
                            if self.state.options_list:
                                self.state('music search results')
                                self.state.keyboard_type = 'options list'
                            else:
                                self.state('music menu')
                                self.state.keyboard_type = 'music'
                        else:
                            logger.info('search action:', self.remove_unicode(command))
                            if (('add' in command) or ('play' in command)
                                                   or ('shuffle' in command)):
                                self.state('music menu')
                                self.state.keyboard_type = 'music menu'
                                if ('play' in command) or ('shuffle' in command):
                                    self.state.mopidy.clear()
                                load_state = 'loading'
                                load_state = self.state.mopidy.load(self.state.uri,'uri')
                                while load_state=='loading':
                                    pass # Wait until the uri is loaded
                                if load_state:
                                    if ('play' in command) or ('shuffle' in command):
                                        if 'shuffle' in command:
                                            self.state.mopidy.shuffle()
                                        end_of_command_refresh = False
                                        self.state.music_status.mopidy_playing = True
                                        self.state.mopidy.play()
                                    self.state.set_reply_text('Rock it!')
                                    self.state.uri = False
                                else:
                                    self.state.options_list = False
                                    self.state.uri_list = False
                                    self.state.set_reply_text('Error loading')
                            elif 'albums' in command:
                                [albums_list,uri_list] = self.state.mopidy.albums_spotify(
                                                        self.state.uri)
                                self.state.options_list = albums_list
                                self.state.uri_list = uri_list
                                self.state('music search results')
                                self.state.keyboard_type = 'options list'
                                self.state.set_reply_text('Found this')
                            elif 'tracks' in command:
                                [tracks_list,uri_list] = self.state.mopidy.tracks_spotify(
                                                        self.state.uri)
                                self.state.options_list = tracks_list
                                self.state.uri_list = uri_list
                                self.state('music search results')
                                self.state.keyboard_type = 'options list'
                                self.state.set_reply_text('Found this')
                            elif 'wake up sound' in command:
                                self.state('music menu')
                                self.state.keyboard_type = 'music menu'
                                self.state.alarm.set_config('ring_music',self.state.uri)
                                self.state.uri = False
                                self.state.set_reply_text('Nice choice!')
                            else:
                                self.state.set_reply_text('Command not recognized')
                elif '/return' in command:
                    self.state('music')
                    self.state.keyboard_type = 'home home'
                else:
                    self.state.set_reply_text('Command not recognized')
                    
                '''Alarm clock controls'''
        elif 'alarm' in self.state():
            end_of_command_refresh = True
            self.state.auto_refresh_enabled = False
            if ' view' in self.state():
                if 'set_alarm' in command:
                    split_command = self.remove_unicode(command).split(':')
                    if len(split_command) > 1:
                        self.state.set_alarm_day = int(split_command[1])
                        self.state('alarm set on_day')
                        self.state.keyboard_type = 'alarm set on_day'
                        logger.info('set_alarm')
                    else:
                        self.state.set_reply_text('Write the time in "HH:MM"')
                elif 'temporizer' in command:
                    self.state('alarm set temporizer')
                    self.state.keyboard_type = 'options list'
                    self.state.options_list = self.alarm.temporizer_options_list()
                    self.state.set_reply_text('How many minutes?')
                elif 'change_config' in command:
                    self.state('alarm change_config config_view')
                    self.state.keyboard_type = 'return'
                elif '/return' in command:
                    self.state('music')
                    self.state.keyboard_type = 'home home'
                else:
                    [h,m,success] = self.format_time(command)
                    if success:
                        if (self.alarm.to_localtime(datetime.datetime.utcnow()).time() >
                            datetime.time(hour=h,minute=m)):
                            delta_day = 1
                        else:
                            delta_day = 0
                        set_datetime = datetime.timedelta(days=delta_day,
                                                          hours=h,minutes=m)
                        self.alarm.set_manual_alarm_localtime(set_datetime)
                        self.state('alarm view')
                        self.state.keyboard_type = 'alarm menu'
                    else:
                        self.state.set_reply_text('Bad format -> "HH:MM"')
            elif ' set' in self.state():
                if '/return' in command:
                    self.state('alarm view')
                    self.state.keyboard_type = 'alarm menu'
                elif 'on_day' in self.state():
                    if 'add new' in command:
                        self.state.set_reply_text('Write the time in "HH:MM"')
                    elif 'edit' in command:
                        [h,m,success] = self.format_time(command)
                        alarm_type = []
                        if u'\U0001F3E7' in command:
                            alarm_type.append('auto')
                        else:
                            alarm_type.append('manual')
                        if u'\U0001F51B' in command:
                            alarm_type.append('enabled')
                        else:
                            alarm_type.append('disabled')
                        temp_value = datetime.datetime(100,1,1,hour=h,minute=m)
                        self.state.alarm_to_edit = [alarm_type,(self.alarm.to_utc(temp_value)).time()]
                        self.state('alarm edit')
                        self.state.keyboard_type = 'alarm edit'
                    elif 'set_alarm' in command:
                        split_command = self.remove_unicode(command).split(':')
                        if len(split_command) > 1:
                            self.state.set_alarm_day = int(split_command[1])
                        else:
                            self.state.set_alarm_day = 0
                        self.state('alarm set on_day')
                        self.state.keyboard_type = 'alarm set on_day'
                    else:
                        [h,m,success] = self.format_time(command)
                        if success:
                            set_datetime = datetime.timedelta(days=self.state.set_alarm_day,
                                                              hours=h,minutes=m)
                            self.alarm.set_manual_alarm_localtime(set_datetime)
                            self.state('alarm view')
                            self.state.keyboard_type = 'alarm menu'
                        else:
                            self.state.set_reply_text('Bad format -> "HH:MM"')
                elif 'temporizer' in self.state():
                    if command.isdigit():
                        if int(command)<720 or int(command)<=0:
                            set_datetime = self.alarm.build_temporizer_timedelta(int(command))
                            self.alarm.set_manual_alarm(set_datetime)
                            self.state('alarm view')
                            self.state.keyboard_type = 'alarm menu'
                            self.state.set_reply_text('Done')
                        else:
                            self.state.set_reply_text('Up to 12 hours')
                    else:
                        self.state.set_reply_text('Bad format -> "Minutes"')
            elif ' edit' in self.state():
                if 'change' in command:
                    self.state.set_reply_text('Write change time in "HH:MM"')
                elif 'delete' in command or 'disable' in command or 'enable' in command:
                    if 'disable' in command or 'enable' in command:
                        command = 'toggle'
                    if self.alarm.edit_alarm(self.state.set_alarm_day,self.state.alarm_to_edit[1],
                                             self.remove_unicode(command)):
                        self.state('alarm view')
                        self.state.keyboard_type = 'alarm menu'
                    else:
                        self.state.set_reply_text('Error editing alarm')
                else:
                    [h,m,success] = self.format_time(command)
                    if success:
                        temp_value = datetime.datetime(100,1,1,hour=h,minute=m)
                        change_time = (self.alarm.to_utc(temp_value)).time()
                        if self.alarm.edit_alarm(self.state.set_alarm_day,self.state.alarm_to_edit[1],
                                                 'change',change_time):
                            self.state('alarm view')
                            self.state.keyboard_type = 'alarm menu'
                        else:
                            self.state.set_reply_text('Error editing alarm')
                    else:
                        self.state.set_reply_text('Bad format -> "HH:MM"')
            elif 'change_config' in self.state():
                if self.alarm.is_config(command):
                    self.state.set_config_name = command
                    self.state('alarm change_config_edit')
                    self.state.keyboard_type = 'options list'
                    self.state.options_list = self.state.alarm.config_options_list(command)
                    units = self.alarm.get_config_units(command)
                    self.state.set_reply_text(units)
                elif 'config_view' in self.state():
                    if '/return' in command:
                        self.state('alarm view')
                        self.state.keyboard_type = 'alarm menu'
                    else:
                        self.state.set_reply_text('Command not recognized')
                elif 'edit' in self.state():
                    if '/return' in command:
                        self.state('alarm change_config config_view')
                        self.state.keyboard_type = 'return'
                    else:
                        result = self.state.alarm.set_config(self.state.set_config_name,command)
                        self.state.set_reply_text(result)
            else:
                self.state.set_reply_text('Command process fail')
        
            '''Alarm clock ringing'''
        elif 'ringing' in self.state() or 'snooze' in self.state():
            end_of_command_refresh = True
            self.state.auto_refresh_enable = False
            if self.alarm.c.alarm_stop_password in command:
                self.state.snooze_counts = 0
                if not self.alarm.edit_closest_alarm('disable'):
                    self.state.set_reply_text('Alarm not disabled')
                else:
                    self.state.set_reply_text('Alarm disabled')
                self.state('music')
                self.state.keyboard_type = 'home home'
                self.state.mopidy.set_volume_sys(self.state.default_volume)
                self.state.mopidy.clear()
                self.state.auto_refresh_enable = True
            elif 'ringing' in self.state() and'/snooze' in command:
                if self.state.snooze_counts < int(self.alarm.c.max_snooze_counts):
                    self.state.snooze_counts += 1
                    if not self.alarm.edit_closest_alarm('snooze'):
                        set_datetime = self.alarm.build_temporizer_timedelta(int(self.alarm.c.snooze_min))
                        self.alarm.set_manual_alarm(set_datetime)
                    self.state('snooze')
                    self.state.keyboard_type = 'nothing'
                    self.state.mopidy.clear()
                else:
                    self.state.set_reply_text('Enough snooze')
            else:
                if '/time' in command:
                    self.state.set_reply_text('Time to wake up!')
                else:
                    self.state.set_reply_text('Type:'+self.alarm.c.alarm_stop_password,
                                              dash_join=False)

            '''General Configuration'''
        elif 'general_config' in self.state():
            end_of_command_refresh = True
            self.state.auto_refresh_enabled = False
            if 'set_password' in command:
                self.state('general_config set_password')
                self.state.keyboard_type = 'return'
                self.state.set_reply_text('Type the new password')
            elif 'add_calendar' in command:
                self.state('general_config add_calendar')
                self.state.keyboard_type = 'return'
                self.state.set_reply_text('Send the url to add')
            elif 'remove_calendar' in command:
                self.state('general_config remove_calendar')
                self.state.keyboard_type = 'options list'
                self.state.options_list = self.state.cal_check.get_cal_urls()
                self.state.set_reply_text('Choose the url to remove')
            elif 'default_volume' in command:
                self.state('general_config default_volume')
                self.state.keyboard_type = 'options list'
                self.state.options_list = list(range(10,110,10))
                self.state.set_reply_text('Choose the volume %')
            elif 'view' in self.state():
                if '/return' in command:
                    self.state('music')
                    self.state.keyboard_type = 'home menu'
                else:
                    self.state.set_reply_text('Command not recognized')
            else:
                if '/return' in command:
                    self.state('general_config view')
                    self.state.keyboard_type = 'return'
                else:
                    if 'set_password' in self.state():
                        self.config.set_section('Password',command.strip())
                        self.state.set_reply_text('Done')
                    elif 'add_calendar' in self.state():
                        self.state.cal_check.add_cal_url(command.strip())
                        self.state.set_reply_text('Done')
                    elif 'remove_calendar' in self.state():
                        if self.state.cal_check.remove_cal_url(command.strip()):
                            self.state.set_reply_text('Done')
                        else:
                            self.state.set_reply_text('Calendar not in the list')
                    elif 'default_volume' in self.state():
                        if int(command)<=100 and int(command)>0:
                            self.state.set_default_control('volume',command)
                            self.state.default_volume = self.state.get_default_control("volume")
                            self.state.set_reply_text('Done')
                        else:
                            self.state.set_reply_text('Volume between 0 and 100')
                    self.state('general_config view')
                    self.state.keyboard_type = 'return'

        '''End of Command Process'''
        if end_of_command_refresh:
            self.state.refresh_dashboard()    

    def selection_process(self,command):
        '''Returns the uri corresponding to the selected option in te option list'''
        for index,option in enumerate(self.state.options_list):
            if command in option:
                return self.state.uri_list[index]
        return False

    def format_time(self,command):
        '''Parses the command to return hours and minutes in the desired format 
           and checks validity'''
        success = False
        hours = 0
        minutes = 0
        command = self.remove_unicode(command)
        if len(command.split('-')) > 1:
            command = command.split('-')[1]
        command_split = command.split(':')
        if len(command_split) == 2:
            try:
                hours = int(command_split[0])
                minutes = int(command_split[1])
                if (hours<24) and (hours>=0) and (minutes<60) and (minutes>=0):
                    success = True
            except:
                success = False
        return [hours,minutes,success]
    
    def remove_unicode(self,string):
        '''Removes the unicode characters of a string'''
        return ''.join([x for x in string if ord(x) < 255])

    def reboot(self):
        logger.info('Reebot asked')
        for chat_id in self.state.chat_id_list:
            self.bot.sendMessage(chat_id, 'Reboot asked')
        os.execv(self.state.config.path+'main.py',[''])
        return

    def update(self):
        logger.info('Update and reboot asked')
        for chat_id in self.state.chat_id_list:
            self.bot.sendMessage(chat_id, 'Update and reboot asked')
        subprocess.check_output(['cd',self.state.config.path])
        subprocess.check_output(['git','pull','origin,master'])
        logger.info('Update completed')
        os.execv(self.state.config.path+'main.py',[''])
        return

    def restart_raspotify(self):
        logger.info('Restart raspotify')
        subprocess.check_output(['sudo','systemctl','restart','raspotify'])
        for chat_id in self.state.chat_id_list:
            self.bot.sendMessage(chat_id, 'Spotify device restarted\n'
                                 +'Check internet connection if still fails')
        return
