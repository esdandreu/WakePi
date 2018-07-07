from __future__ import unicode_literals

import datetime
import requests
from icalendar import Calendar, Event
from configcontrols import ConfigControls

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
        print('INFO: Getting week calendar')
        today = datetime.datetime.utcnow().date()
        next_week = today + datetime.timedelta(7)
        week_cal = Calendar()
        week_cal.add('x-wr-calname', "Weekly Combined Calendar")
        urls = self.get_cal_urls()
        for url in urls:
            try:
                req = requests.get(url)#usual source of error
                if req.status_code != 200:
                    print("Error {} fetching {}: {}"
                          .format(url, req.status_code, req.text))
                    continue
                cal = Calendar.from_ical(req.text)
                for event in cal.walk("VEVENT"):
                    end = event.get('dtend')
                    if end:
                        if hasattr(end.dt, 'date'):
                            date = end.dt.date()
                        else:
                            date = end.dt
                        if date >= today and date < next_week:
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
                print('WARNING: invalid calendar, removing')
                print(url)
                print(error)
                self.remove_cal_url(url)
                for chat_id in self.state.chat_id_list:
                    self.state.bot.sendMessage(chat_id,'Removed invalid calendar url:\n'+url)
        print('INFO: Got calendars')
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
            start = event.get('dtstart')
            if start:
                event_start = start.dt.replace(tzinfo=None)
                event_start_local = event_start + utcoffset
                days_to_go = event_start_local.weekday()-today_local.weekday()
                if days_to_go<0:
                    days_to_go += 7
                events[days_to_go].append(event_start_local)
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


        
   
