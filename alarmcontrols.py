from __future__ import unicode_literals

import datetime
import pickle
import numpy
import os
from mopidycontrols import MopidyControls
from calendarcheck import CalendarCheck
from configcontrols import ConfigControls
from collections import namedtuple
import sys
import logging
logger = logging.getLogger('WakePi')

class AlarmControls:
    def __init__(self,state):
        self.state = state
        self.cal_check = CalendarCheck(self.state)
        self.config = ConfigControls()
        '''Config'''
        self.c = self.get_config()
        self.RING_TIME_THRESHOLD = 15 #[seconds]
        
    def ring(self):
        '''Plays the alarm music'''
        while self.state.auto_refresh_enabled: 
            self.state.auto_refresh_enabled = False
        self.state.music_status.mopidy_playing = True
        self.state.mopidy.clear()
        self.state.mopidy.repeat('on')
        self.state.mopidy.random('on')
        if not self.state.mopidy.load(self.c.ring_music,'uri'):
            logger.warning('Local file loaded for ringing')
            self.state.mopidy.load_local_song()
        self.state.mopidy.shuffle()
        self.state.mopidy.play()
        self.state.mopidy.set_volume_sys(int(self.c.ring_start_volume))
        self.state('ringing')
        self.state.keyboard_type = 'ringing'
        self.state.refresh_dashboard()

    def set_ring_volume(self,ringing_time):
        '''Sets the ring volume according to two linear relationships, one for the first
           half volume augment and the other until the maximum ringing volume'''
        if ringing_time <= self.c.half_ring_volume_sec:
            vol_slope = (((self.c.max_ringing_volume-self.c.ring_start_volume)/2)
                            /self.c.half_ring_volume_sec)
            volume = int(self.c.ring_start_volume+vol_slope*ringing_time)
        elif ringing_time <= self.c.max_ring_volume_sec:
            vol_slope = (((self.c.max_ringing_volume-self.c.ring_start_volume)/2)
                            /(self.c.max_ring_volume_sec-self.c.half_ring_volume_sec))
            volume = int((self.c.max_ringing_volume+self.c.ring_start_volume)/2
                         +vol_slope*(ringing_time-self.c.half_ring_volume_sec))
        else:
            volume = int(self.c.max_ringing_volume)
        volume = min(volume,int(self.c.max_ringing_volume))
        self.state.mopidy.set_volume_sys(volume)
    
    def get_alarms(self):
        '''Gets the alarm string array from the saved file'''
        file = open(os.path.join(self.config.path,"saved_alarms.py"),"rb")
        alarms = pickle.load(file)
        file.close()
        return alarms

    def get_config(self):
        try:
            text_config = self.config.get_section('Alarm Controls')
            config_name_list = []
            for line in text_config:
                config_name_list.append(line.split('=')[0].split('(')[0].strip())
            config_list = namedtuple('config_list',
                                     ' '.join(config_name_list))
            for line in text_config:
                for config_name in config_list._fields:
                    if config_name in line:
                        config_value = line.split(' = ')[1].strip()
                        if config_value.isdigit():
                            config_value = int(config_value)
                        setattr(config_list,config_name,config_value)
            return config_list
        except:
            # Put here the default control values
            logger.error("Bad AlarmControls config, default config applied: {}".format(sys._getframe(  ).f_code.co_name))
            return config_list(10,30,70,14,35,30,60,10,6,10,"I am awake",
                               'spotify:user:2155eprgg73n7x46ybpzpycra:playlist:64xSAgfPBl8HjIKJBi3CIi')

    def get_config_units(self,config_name):
        if 'time' in config_name or 'min' in config_name:
            units = '(minutes)'
        elif 'sec' in config_name:
            units = '(seconds)'
        elif 'volume' in config_name:
            units = '(%)'
        elif 'counts' in config_name:
            units = '(-)'
        else:
            units = ''
        return units
    
    def set_alarms(self,alarms):
        '''Saves the alarm string array to the file'''
        file = open(os.path.join(self.config.path,"saved_alarms.py"),"wb")
        pickle.dump(alarms,file)
        file.close()
        return

    def set_config(self,config_name,config_value):
        '''Saves the config parameter in the text file and checks the value'''
        if 'ring_music' in config_name:
            if config_value.isdigit():
                return 'Bad URI format'
        elif 'alarm_stop_password' in config_name:
            if len(config_value)>100:
                return "Don't be silly"
            elif '/' in config_value:
                return 'invalid key "/"'
        else:
            if not config_value.strip().isdigit():
                return 'Must be a positive number'
            else:
                if ('snooze_min' in config_name or
                    'max_snooze_counts' in config_name):
                    if int(config_value)==0:
                        return 'Must be greater than 0'
                    if 'snooze_min' in config_name:
                        if int(config_value)>30:
                            return 'Snooze up to 30 min'
                    elif 'max_snooze_counts' in config_name:
                        if int(config_value)>1000:
                            return "Don't be silly"
                elif ('ring_start_volume' in config_name or
                    'max_ringing_volume' in config_name):
                    if int(config_value)>100:
                        return 'Up to 100%'
                    if 'ring_start_volume' in config_name:
                        if int(config_value)>int(self.c.max_ringing_volume):
                            return "Start Vol(<)Max Vol"
                    elif 'max_ringing_volume' in config_name:
                        if int(config_value)<int(self.c.ring_start_volume):
                            return "Max Vol(>)Start Vol"
                elif 'max_ringing_time' in config_name:
                    if int(config_value)<5 or int(config_value)>60:
                        return 'Between 5 and 60'
                elif 'event_time_before' in config_name:
                    #first_event_time_before and other_event_time_before
                    if int(config_value)>360:
                        return 'Up to 6 hours before'
                elif 'ring_volume_sec' in config_name:
                    #max_ring_volume_time and half_ring_volume_time
                    if int(config_value)>180:
                        return 'Up to 3 minutes'
                    elif 'max' in config_name:
                        if int(config_value)<int(self.c.half_ring_volume_sec):
                            return 'Max Time(>)Half Time'
                    elif 'half' in config_name:
                        if int(config_value)>int(self.c.max_ring_volume_sec):
                            return 'Half Time(<)Max Time'
                elif 'ring_refresh_sec' in config_name:
                    if int(config_value)>60 or int(config_value<5):
                        return 'Betweeen 5 and 60 seconds'
                else:
                    return 'Config name not recognized!'
        unit = self.get_config_units(config_name)
        if unit == '':
            setattr(self.c,config_name,str(config_value))
        else:
            setattr(self.c,config_name,int(config_value))
        config_list = []
        for name in self.c._fields:
            value = getattr(self.c,name)
            units = self.get_config_units(name)
            if isinstance(value,int):
                value = str(value)
            config_list.append(name +' '+ units + ' = ' + value)
        self.config.set_section('Alarm Controls',config_list)
        return 'Your wishes are orders'          

    def is_config(self,config_name):
        '''Says if a name is a configuration name'''
        for name in self.c._fields:
            if config_name in name:
                return True
        return False

    def config_options_list(self,config_name):
        options_list = []
        if 'ring_music' in config_name:
            return False
        else:
            if 'snooze_min' in config_name:
                options_list = list(range(5,35,5))
            elif 'max_snooze_counts' in config_name:
                options_list = list(range(1,11,1))
            elif 'ring_start_volume' in config_name:
                options_list = list(range(0,int(self.c.max_ringing_volume),5))
            elif 'max_ringing_volume' in config_name:
                options_list = list(range(int(self.c.ring_start_volume),105,5))
            elif 'max_ringing_time' in config_name:
                options_list = list(range(5,35,5))
            elif 'event_time_before' in config_name:
                #first_event_time_before and other_event_time_before
                options_list = list(range(0,135,15))
            elif 'alarm_stop_password' in config_name:
                options_list = ["I am awake"]
            elif 'half_ring_volume_sec' in config_name:
                options_list = list(range(0,int(self.c.max_ring_volume_sec),2))
            elif 'max_ring_volume_sec' in config_name:
                options_list = list(range(int(self.c.half_ring_volume_sec),60,5))
            elif 'ring_refresh_sec' in config_name:
                options_list = list(range(10,70,10))
            else:
                return False
        return options_list

    def temporizer_options_list(self):
        temp_list = list(range(5,30,5))
        temp_list.extend(list(range(30,75,15)))
        return temp_list
    
    def alarm_str2time(self,alarm_str):
        ''' Format the alarm string to time '''
        separator = alarm_str.find('-')
        if separator >= 0:
            alarm_type = alarm_str[:separator]
            alarm_type = alarm_type.split(' ')
            alarm_time = alarm_str[(separator+1):]
            alarm_time = datetime.datetime.strptime(alarm_time,'%c')
            return [alarm_type, alarm_time]
        else:
            logging.error("Bad alarm format: {} ".format(sys._getframe(  ).f_code.co_name))
            return [False, False]

    def alarm_time2str(self,alarm_type,alarm_time):
        ''' Format the alarm time to string '''
        alarm_type_str = ' '.join(alarm_type)
        alarm_time_str = alarm_time.strftime('%c')
        alarm_str = '-'.join([alarm_type_str,alarm_time_str])
        return alarm_str

    def to_localtime(self,d):
        '''Localtime defined by the raspberry localtime'''
        utcoffset = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)
        if d is not None:
            return d+utcoffset
        else:
            return None

    def to_utc(self,d):
        utcoffset = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)
        if d is not None:
            return d-utcoffset
        else:
            return None
    
    def set_auto_alarms(self,week_events):
        '''Sets the alarms acording to the first event of the day'''
        alarms = self.get_alarms()
        now_local = self.to_localtime(datetime.datetime.utcnow())
        today = now_local.date()
        new_alarms = []
        first_event_time_before = datetime.timedelta(minutes=int(self.c.first_event_time_before))
        auto_alarm_disabled = [False,False,False,False,False,False,False]
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            if alarm_time.date()-today >= datetime.timedelta(0):
                if 'auto' in alarm_type[0]:
                    if 'enabled' in alarm_type[1]:
                        pass # We delete enabled auto alarms and update them later
                    else:#We mark the disabled auto alarms to chekc update
                        days_to_go = (self.to_localtime(alarm_time).weekday()
                                      -today.weekday())
                        if days_to_go < 0:
                            days_to_go += 7
                        auto_alarm_disabled[days_to_go] = alarm_time
                else:
                    # We keep all manual alarms not outdated
                    new_alarm = self.alarm_time2str(alarm_type,alarm_time)
                    new_alarms.append(new_alarm)
            else:
                pass #if the alarm is outdated we delete it
        first_events_localtime = self.cal_check.get_day_first_events_localtime(
                                                week_events)
        first_events = [self.to_utc(item) for item in first_events_localtime]
        for day,event in enumerate(first_events):
            if event is not None: # if there is an event we update the alarm
                if auto_alarm_disabled[day]:
                    if event-first_event_time_before < auto_alarm_disabled[day]:
                        # if the event is earlier than the diabled event we enable it
                        new_alarm = self.alarm_time2str(['auto','enabled'],
                                                event-first_event_time_before)
                        new_alarms.append(new_alarm)
                    else:
                        # if the event is later than the disabled event we keep it disabled
                        new_alarm = self.alarm_time2str(['auto','disabled'],
                                                event-first_event_time_before)
                        new_alarms.append(new_alarm)
                else: # if the event was enabled or the event is new we keep it enabled
                    new_alarm = self.alarm_time2str(['auto','enabled'],
                                                event-first_event_time_before)
                    new_alarms.append(new_alarm)
            else: #if there is no event now we delete the auto alarm
                pass
        new_alarms = list(set(new_alarms)) #This removes the duplicates
        self.set_alarms(new_alarms)
        return True

    def build_temporizer_timedelta(self,temp_minutes):
        now = datetime.datetime.utcnow()
        return datetime.timedelta(0,hours=now.hour,minutes=now.minute+temp_minutes)
    
    def set_manual_alarm(self,set_datetime):
        '''Sets a manual alarm some days after at a desired time
           set_datetime = datetime.timedelta(day_increase,set_time)
           '''
        today = datetime.datetime.utcnow().date()
        new_alarm = (datetime.datetime.combine(today, datetime.time(0))
                     + set_datetime)
        repeated = False
        alarms= self.get_alarms()
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            if abs((alarm_time-new_alarm).total_seconds()) <= 60:
                repeated = True
        if not repeated:
            new_alarm_str = self.alarm_time2str(['manual','enabled'],new_alarm)
            alarms.append(new_alarm_str)
            self.set_alarms(alarms)
            return
        else:
            return

    def set_manual_alarm_localtime(self,set_datetime):
        '''Sets a manual alarm some days after at a desired time on the local
           timezone
           set_datetime = datetime.timedelta(day_increase,set_time)
           '''
        utcoffset = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)
        today = (datetime.datetime.utcnow()+utcoffset).date()
        new_alarm = (datetime.datetime.combine(today, datetime.time(0))
                     + set_datetime - utcoffset)
        repeated = False
        alarms = self.get_alarms()
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            if abs((alarm_time-new_alarm).total_seconds()) <= 60:
                repeated = True
        if not repeated:
            new_alarm_str = self.alarm_time2str(['manual','enabled'],new_alarm)
            alarms.append(new_alarm_str)
            self.set_alarms(alarms)
            return
        else:
            return
        
    def alarm_check(self):
        '''Checks if an alarm time has been reached and rings acordingly'''
        alarms = self.get_alarms()
        now = datetime.datetime.utcnow()
        min_time_to_ring = 24*60*60
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            ''' Check only enabled alarms '''
            if 'enabled' in alarm_type[1]:
                time_to_ring = (alarm_time-now).total_seconds()
                if time_to_ring<0:
                    time_to_ring = 24*60*60
                min_time_to_ring = min(min_time_to_ring,time_to_ring)
                if time_to_ring <= self.RING_TIME_THRESHOLD:
                    self.ring()
                    return 0
        return min_time_to_ring

    def edit_closest_alarm(self,action):
        '''Edits the closest alarm acording to the input action,
           useful for disable the alarm that is ringing now or activate snooze mode
           '''
        alarms = self.get_alarms()
        now = datetime.datetime.utcnow()
        success = False
        for index,alarm in enumerate(alarms):
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            ''' Check only enabled alarms '''
            if 'enabled' in alarm_type[1]:
                if 'disable' in action:
                    if ((alarm_time-now).total_seconds() <= 11*60
                        and (now-alarm_time).total_seconds() <= 20*60):
                        alarm_type[1] = 'disabled'
                        success = True
                        logger.info('Alarm disabled')
                elif 'snooze' in action:
                    if ((alarm_time-now).total_seconds() <= 60
                        and (now-alarm_time).total_seconds() <= 20*60):
                        alarm_time = alarm_time + datetime.timedelta(
                                                minutes=self.c.snooze_min)
                        success = True
                alarms[index] = self.alarm_time2str(alarm_type,alarm_time)
        self.set_alarms(alarms)
        return success

    def edit_alarm(self,days_to_go,alarm_time,action,change_time=None):
        '''Edits an alarm configuration acording to the input action'''
        today = self.to_localtime(datetime.datetime.utcnow())
        edit_alarm_time = datetime.datetime.combine(
                        today+datetime.timedelta(days=days_to_go),alarm_time)
        alarms = self.get_alarms()
        new_alarms = []
        success = False
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            if abs((alarm_time-edit_alarm_time).total_seconds()) < 60:
                if 'toggle' in action:
                    if 'disabled' in alarm_type[1]:
                        alarm_type[1] = 'enabled'
                    else:
                        alarm_type[1] = 'disabled'
                elif 'change' in action:
                    if change_time is None:
                        logger.error("Bad imput: {}".format(sys._getframe(  ).f_code.co_name))
                        success = False
                        return success
                    else:
                        if 'manual' in alarm_type[0]:
                            alarm_time = datetime.datetime.combine(
                                today+datetime.timedelta(days=days_to_go),
                                change_time)
                        else: #When changing auto alarms, disable auto and create new manual
                            alarm_type[1] = 'disabled'
                            new_alarm_time = datetime.datetime.combine(
                                today+datetime.timedelta(days=days_to_go),
                                change_time)
                            new_alarms.append(self.alarm_time2str(
                                ['manual','enabled'],new_alarm_time))
                if not 'delete' in action:
                    new_alarms.append(self.alarm_time2str(alarm_type,alarm_time))
                success = True
            else:
                new_alarms.append(self.alarm_time2str(alarm_type,alarm_time))
        self.set_alarms(new_alarms)
        return success
        

    def get_week_alarms_localtime(self):
        '''Gets a list of alarms ordered by day, and time,
           today alarms are on week_alarms[0], today first alarm is on
           week_alarms[0][0], tomorrow is on week_alarms[1], etc.
           '''
        today = self.to_localtime(datetime.datetime.utcnow())
        alarms = self.get_alarms()
        week_alarms = [[],[],[],[],[],[],[]]
        for alarm in alarms:
            [alarm_type, alarm_time] = self.alarm_str2time(alarm)
            alarm_time = self.to_localtime(alarm_time)
            '''Check within a week'''
            if ((alarm_time.date()-today.date() >= datetime.timedelta(0))
                and (alarm_time.date()-today.date() < datetime.timedelta(7))):
                weekday = alarm_time.weekday()
                week_alarms[weekday].append([alarm_type,alarm_time.time()])
        sorted_alarms = [[],[],[],[],[],[],[]]
        for weekday, day in enumerate(week_alarms):
            sorted_alarms[weekday] = sorted(day)
        week_alarms = numpy.roll(sorted_alarms,-today.weekday()).tolist()
        return week_alarms

    def build_msg_text_from_alarms(self):
        '''Builds a msg_txt from the alarms set on the week
           in a very specific format, shows also the alarm type
           '''
        today = self.to_localtime(datetime.datetime.utcnow())
        today_weekday = today.weekday()
        week_alarms = self.get_week_alarms_localtime()
        _type=0
        _time=1
        max_length = 0
        for day in week_alarms:
            if len(day) > max_length:
                max_length = len(day)
        alarm_list = []
        for x in range(0,max_length):
            hours_list = []
            minut_list = []
            type_list = []
            for day in week_alarms:
                if x < len(day):
                    if 'disabled' in day[x][_type][1]:
                        hours_list.append(day[x][_time].strftime("x%H|"))
                    else:
                        hours_list.append(day[x][_time].strftime(" %H|"))
                    minut_list.append(day[x][_time].strftime(":%M|"))
                    if 'auto' in day[x][_type][0]:
                        type_list.append('-A-|')
                    else:
                        type_list.append('---|')
                else:
                    hours_list.append('   |')
                    minut_list.append('   |')
                    type_list.append( '---|')
            hours_str = ''.join(hours_list)
            minut_str = ''.join(minut_list)
            type_str  = ''.join(type_list )
            alarm_list.append('`'+type_str.strip( '|')+'`')
            alarm_list.append('`'+hours_str.strip('|')+'`')
            alarm_list.append('`'+minut_str.strip('|')+'`')
        num_list = []
        month_list = []
        for x in range(0,7):
            day = today+datetime.timedelta(x)
            month_list.append(day.strftime('%B')[:3]+'|')
            num_list.append(day.strftime(' %d|'))
        name_list = ['Mon|','Tue|','Wed|','Thu|','Fri|','Sat|','Sun|']
        name_list = numpy.roll(name_list,-today_weekday).tolist()
        msg_text = ''.join(['`'+''.join(name_list).strip('|')+'`'+'\n',
                            '\n'.join(alarm_list)+'\n',
                            '`'+''.join(month_list).strip('|')+'`'+'\n',
                            '`'+''.join(num_list).strip('|')+'`'])
        t = self.alarm_check()
        hours = str(int(t/3600)%24)
        if len(hours)<2:
            hours = '0'+hours
        minutes = str(int(t/60)%60)
        if len(minutes)<2:
            minutes = '0'+minutes
        last_line =  ('`--`'+
                      u'\U0001F567'+u'\U0001F552'+u'\U000023F3'+u'\U000027A1'
                      +'` `'+hours[0]+u'\U000020E3'+hours[1]+u'\U000020E3'
                      +'*:*'+minutes[0]+u'\U000020E3'+minutes[1]+u'\U000020E3'
                      +u'\U0001F555'+u'\U0001F55B'+'`--`')
        msg_text = '\n'.join([msg_text,last_line])
        return msg_text
