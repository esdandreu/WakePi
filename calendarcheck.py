from __future__ import unicode_literals

import datetime
import requests
import json
from icalendar import Calendar, Event
from configcontrols import ConfigControls
import sys
import logging
logger = logging.getLogger('WakePi')

class CalendarCheck:
    def __init__(self,state):
        self.state = state
        self.config = ConfigControls()
        
    def get_cal_urls(self):
        '''Gets the calendars urls from the config.txt'''
        urls = self.config.get_section('Calendar')
        return urls

    def add_cal_url(self,url):
        '''Adds a url to the config file'''
        urls = self.get_cal_urls()
        urls.append(url)
        self.config.set_section('Calendar',urls)
        return True

    def remove_cal_url(self,url):
        urls = self.get_cal_urls()
        try:
            urls.remove(url)
            self.config.set_section('Calendar',urls)
            return True
        except:
            return False
    
    def get_week_cal(self):
        '''Extracts the weekly calendar from the ical urls on the config file'''
        logger.info('Getting week calendar')
        today = datetime.datetime.utcnow().date()
        next_week = today + datetime.timedelta(7)
        week_cal = Calendar()
        week_cal.add('x-wr-calname', "Weekly Combined Calendar")
        urls = self.get_cal_urls()
        for url in urls:
            logger.debug(url)
            try:
                # Error avoider: Tries to read the calendar several times
                attempts = 0
                while attempts < 5:
                    if attempts < 4:
                        try:
                            req = requests.get(url)
                            attempts=5
                        except:
                            attempts += 1
                    else:
                        req = requests.get(url)
                        attempts=5
                # Error avoider finished
                if req.status_code != 200:
                    logger.error("Error {} fetching {}: {}"
                          .format(url, req.status_code, req.text))
                    continue
                cal = Calendar.from_ical(req.text)
                for event in cal.walk("VEVENT"):
                    end = event.get('dtend')
                    if end:
                        WEEK_EVENT = False
                        if hasattr(end.dt, 'date'):
                            date = end.dt.date()
                        else:
                            date = end.dt
                        if date >= today and date < next_week:
                            WEEK_EVENT = True
                        elif 'RRULE' in event:
                            try:
                                rrule = event['RRULE']
                                until = rrule.get('until')[0]
                                if today < until.date():
                                    # Only weekly repeated events are supported
                                    if 'WEEKLY' in rrule.get('freq')[0]:
                                        WEEK_EVENT = True
                                        logger.debug(date)
                            except Exception as error:
                                logger.error(("{} rrule\n" + error).format(sys._getframe(  ).f_code.co_name))
                        if WEEK_EVENT:
                            copied_event = Event()
                            for attr in event:
                                if type(event[attr]) is list:
                                    for element in event[attr]:
                                        copied_event.add(attr, element)
                                else:
                                    copied_event.add(attr, event[attr])
                            week_cal.add_component(copied_event)
            except Exception as error:
                # Add counter to avoid false errors
                logger.warning('Invalid calendar, removing\n'+url+'\n'+error)
                self.remove_cal_url(url)
                for chat_id in self.state.chat_id_list:
                    self.state.bot.sendMessage(chat_id,'Removed invalid calendar url:\n'+url)
        logger.info('Got calendars')
        return week_cal

    def get_week_events_local_times(self):
        '''Gets the starting times of the next week events and returns them
           in a list ordered in days remaining
           events = [[datetime.datetime,...], [...], ...]
           '''
        week_cal = self.get_week_cal()
        now = datetime.datetime.utcnow()
        utcoffset = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)
        today_local = (datetime.datetime.utcnow()+utcoffset).date()
        events = [[],[],[],[],[],[],[]]
        for event in week_cal.walk("VEVENT"):
            if 'RRULE' in event:
                # Only weekly repeated events are supported
                try:
                    ref_start = event.get('dtstart')
                    if isinstance(ref_start.dt,datetime.datetime): # Check is not a full day event
                        reference = ref_start.dt.replace(tzinfo=None)
                        rrule = event['RRULE']
                        if 'BYDAY' in rrule:
                            day_list  = rrule.get('byday')
                        elif 'WKST' in rrule:
                            day_list  = rrule.get('wkst')
                        for day in day_list:
                            for index, day_string in enumerate(['MO','TU','WE','TH','FR','SA','SU']):
                                if day in day_string:
                                    reference_weekday = index
                                    break
                            event_add_day = reference_weekday-now.weekday()
                            if event_add_day<0:
                                event_add_day += 7
                            event_day=now.day+event_add_day
                            event_start = datetime.datetime(
                                now.year,now.month,event_day,reference.hour,reference.minute)
                            #Check for excluded dates
                            is_excluded = False
                            if 'EXDATE' in event:
                                exclusions = event.get('exdate')
                                if not isinstance(exclusions, list):
                                    exclusions = [exclusions]
                                for ex_list in exclusions:
                                    for ex_day in ex_list.dts:
                                        if ex_day.dt.replace(tzinfo=None)-event_start == datetime.timedelta(0):
                                            is_excluded = True
                                            break
                            if not is_excluded:
                                event_start_local = event_start # + utcoffset '''I don't know why it is already local'''
                                days_to_go = event_start_local.weekday()-today_local.weekday()
                                if days_to_go<0:
                                    days_to_go += 7
                                events[days_to_go].append(event_start_local)
                except Exception as error:
                    logger.error(" {}: rrule\n{}".format(
                        sys._getframe(  ).f_code.co_name,error))
            else:
                start = event.get('dtstart')
                if start:
                    try:
                        if isinstance(start.dt,datetime.datetime): # Check is not a full day event
                            event_start = start.dt.replace(tzinfo=None)
                            event_start_local = event_start + utcoffset
                            days_to_go = event_start_local.weekday()-today_local.weekday()
                            if days_to_go<0:
                                days_to_go += 7
                            events[days_to_go].append(event_start_local)
                    except Exception as error:
                        logger.error(" {}: not rrule\n{}".format(
                            sys._getframe(  ).f_code.co_name,error))
        for day in events:
            day.sort()
        return events

    def get_day_first_events_localtime(self,week_events):
        '''Gets a list with the first events of each weekday
           first_events = [datetime.time,...]
           '''
        first_events = [None,None,None,None,None,None,None]
        for days_to_go,event in enumerate(week_events):
            if len(event) > 0:
                first_events[days_to_go] = event[0]
        return first_events


        
   
