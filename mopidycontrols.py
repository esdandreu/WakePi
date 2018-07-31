from __future__ import unicode_literals

import sys
import os
import subprocess
import spotipy
import spotipy.util as util
from configcontrols import ConfigControls
from collections import namedtuple

class MopidyControls:
    def __init__(self,state):
        self.state = state
        self.config = ConfigControls()
        self.MAX_SEARCH_RESULTS = 20
        self.spotipy_VERSION = spotipy.VERSION

    def refresh_token(self):
        ''' Get credentials from config.txt '''
        text_spotipy = self.config.get_section('Spotipy')
        for line in text_spotipy:
            if 'username' in line:
                my_username = line.split(' = ')[1].strip()
            elif 'client_id' in line:
                my_client_id = line.split(' = ')[1].strip()
            elif 'client_secret' in line:
                my_client_secret = line.split(' = ')[1].strip()
            elif 'redirect_uri' in line:
                my_redirect_uri = line.split(' = ')[1].strip()
        self.token = util.prompt_for_user_token(my_username,
                                           'user-read-private '+
                                                'user-read-currently-playing '+
                                                'user-modify-playback-state '+
                                                'user-read-playback-state '+
                                                'user-read-recently-played',
                                           client_id=my_client_id,
                                           client_secret=my_client_secret,
                                           redirect_uri = my_redirect_uri)
        self.spotify = spotipy.Spotify(auth=self.token)
        print('INFO: Spotify token refreshed')
        return self.token
        
    def play(self, playlist=None):
        '''play the currently active track'''
        if self.state.music_status.mopidy_playing:
            try:
                if playlist is None:
                    output = subprocess.check_output(['mpc','play'])
                else:
                    output = subprocess.check_output(['mpc','play',playlist])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if not self.state.music_status.playing:
                    self.spotify.start_playback()
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def pause(self):
        '''Pause playback'''
        if self.state.music_status.mopidy_playing:
            try:
                output = subprocess.check_output(['mpc','pause'])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if self.state.music_status.playing:
                    self.spotify.pause_playback()
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def toggle(self):
        '''Toggles play and pause'''
        if self.state.music_status.mopidy_playing:
            try:
                output = subprocess.check_output(['mpc','toggle'])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if self.state.music_status.playing:
                    self.spotify.pause_playback()
                else:
                    self.spotify.start_playback()
                return True
            except:
                print('ERROR: mopidy control error')
                return False
    
    def list_playlist(self):
        '''Outputs a list of playlists'''
        try:
            output = subprocess.check_output(['mpc','lsplaylist'])
            return output.decode('utf-8')
        except:
            print('ERROR: mopidy control error')
            return False

    def search(self,query,type_):
        '''Outputs a list of the search'''
        try:
            output = subprocess.check_output(['mpc','search',type_,query])
            return output.decode('utf-8')
        except:
            print('ERROR: mopidy control error')
            return False

    def mopidy_status(self):
        '''Outputs the state'''
        try:
            output = subprocess.check_output(['mpc'])
            return output.decode('utf-8')
        except:
            print('ERROR: mopidy control error')
            return False
    
    def load(self,name,name_type):
        try:
            if 'playlist' in name_type or 'pl' in name_type:
                output = subprocess.check_output(['mpc','load',name])
            elif 'uri' in name_type:
                print(''.join(['INFO: load: ',name]))
                auto_refresh_enabled = self.state.auto_refresh_enabled
                if 'spotify:user:spotify' in name: #Solves the error adding playlists created by spotify
                    while self.state.auto_refresh_enabled:
                        self.state.auto_refresh_enabled = False
                    [tracks_list,uri_list] = self.tracks_spotify(name)
                    if not tracks_list and not uri_list:
                        print('ERROR: mopidy load control error')
                        return False
                    self.state.send_chat_action('upload_audio')
                    for uri in uri_list:
                        output = subprocess.check_output(['mpc','add',uri])
                    self.state.auto_refresh_enabled = auto_refresh_enabled
                else:
                    try:
                        output = subprocess.check_output(['mpc','add',name])
                    except:
                        if not 'youtube.com' in name:
                            print('WARNING: alternative loading')
                            while self.state.auto_refresh_enabled:
                                self.state.auto_refresh_enabled = False
                            [tracks_list,uri_list] = self.tracks_spotify(name)
                            if not tracks_list and not uri_list:
                                print('ERROR: mopidy load control error')
                                return False
                            self.state.send_chat_action('upload_audio')
                            for uri in uri_list:
                                output = subprocess.check_output(['mpc','add',uri])
                            self.state.auto_refresh_enabled = auto_refresh_enabled
                        else:
                            print('ERROR: mopidy load control error')
                            return False
            else:
                print("ERROR: Bad input")
                output = ''
                return False
            print('INFO: load success')
            return True
        except Exception as error:
            print('ERROR: mopidy load control error')
            print(error)
            while not self.state.auto_refresh_enabled:
                self.state.auto_refresh_enabled = True
            return False

    def load_local_song(self):
        '''Used when no internet connection, loads a local file song'''
        output = subprocess.check_output(['mpc','add','local:track:WakePi_local_song.mp3'])
        return True
    
    def clear(self):
        '''Clears the current play'''
        if self.state.music_status.mopidy_playing:
            try:
                output = subprocess.check_output(['mpc','clear'])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if self.state.music_status.playing:
                    self.spotify.pause_playback()
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def random(self,mode=None):
        '''Toggles random mode'''
        if self.state.music_status.mopidy_playing:
            try:
                if mode is None:
                    output = subprocess.check_output(['mpc','random'])
                elif (mode is 'on') or (mode is 'off'):
                    output = subprocess.check_output(['mpc','random',mode])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if self.state.music_status.random or mode is 'off':
                    self.spotify.shuffle(False)
                else:
                    self.spotify.shuffle(True)
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def repeat(self,mode=None):
        '''Toggles repeat mode'''
        if self.state.music_status.mopidy_playing:
            try:
                if mode is None:
                    output = subprocess.check_output(['mpc','repeat'])
                elif (mode is 'on') or (mode is 'off'):
                    output = subprocess.check_output(['mpc','repeat',mode])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                if self.state.music_status.repeat or mode is 'off':
                    self.spotify.repeat('off')
                else:
                    self.spotify.repeat('context')
                return False
            except:
                print('ERROR: mopidy control error')
                return False

    def next(self):
        '''Next song in list'''
        if self.state.music_status.mopidy_playing:
            try:
                output = subprocess.check_output(['mpc','next'])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                self.spotify.next_track()
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def prev(self):
        '''Previous song'''
        if self.state.music_status.mopidy_playing:
            status = self.get_status()
            song_percentage = status.song_percentage
            try:
                song_percentage = max(min(song_percentage,100),0)
                if song_percentage < 10:
                    output = subprocess.check_output(['mpc','prev'])
                else:
                    output = subprocess.check_output(['mpc','cdprev'])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                self.spotify.previous_track()
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def seek(self,increment):
        '''Seeks a percentage of the song'''
        status = self.get_status()
        song_percentage = status.song_percentage+increment
        if self.state.music_status.mopidy_playing:
            try:
                song_percentage = max(min(song_percentage,100),0)
                song_percentage = str(song_percentage) + '%'
                output = subprocess.check_output(['mpc','seek',song_percentage])
                return False
            except:
                print('ERROR: mopidy control error')
                return False
        else:
            try:
                position_ms = status.duration_s*10*song_percentage
                self.spotify.seek_track(position_ms)
                return True
            except:
                print('ERROR: mopidy control error')
                return False

    def volume_mopidy(self,volume,increase = None):
        '''Changes the volume'''
        try:
            volume = max(min(volume,100),0)
            if increase is None:
                volume_change = str(volume)
            else:
                if increase:
                    volume_change = '+' + str(volume)
                else:
                    volume_change = '-' + str(volume)
            output = subprocess.check_output(['mpc','volume',volume_change])
            return output.decode('utf-8')
        except:
            print('ERROR: mopidy control error')
            return False

    def volume_sys(self,volume_change):
        try:
            volume_perc = self.get_volume_sys()
            new_volume_perc = max(min(volume_perc+volume_change,100),0)
            if self.set_volume_sys(new_volume_perc):
                return True
            else:
                return False
        except:
            return False
    
    def set_volume_sys(self,volume_perc):
        try:
            db = int((106*(volume_perc/2+50)))-10200
            subprocess.check_output(['sudo','amixer','set','PCM','--',str(db)])
            return True
        except:
            return False

    def get_volume_sys(self):
        output = subprocess.check_output(['sudo','amixer','get','PCM'])
        db = int(output.decode("utf-8").split('\n')[-2].split('[')[0].split('Playback')[1].strip(' '))
        volume_perc = int(((db+10200)/106-50)*2)
        return volume_perc

    def shuffle(self):
        '''Shuffles the current playlist'''
        try:
            output = subprocess.check_output(['mpc','shuffle'])
            return True
        except:
            print('ERROR: mopidy control error')
            return False

    #This function only works with spotify
    def search_spotify(self,query,type_):
        '''Improved search function that returns a name and a URI list'''
        try:
            uri_list = []
            search_list = []
            try:
                info = self.spotify.search(q=query,
                                         limit=self.MAX_SEARCH_RESULTS,
                                         type=type_)
            except:
                self.refresh_token()
                info = self.spotify.search(q=query,
                                         limit=self.MAX_SEARCH_RESULTS,
                                         type=type_)
            if 'playlist' in type_:
                for playlist in info['playlists']['items']:
                    uri_list.append(playlist['uri'])
                    info_text = u'\U0001F3A7 \U0001F4DD'  + playlist['name']
                    search_list.append(info_text)
            elif 'track' in type_:
                for track in info['tracks']['items']:
                    uri_list.append(track['uri'])
                    info_text = (u'\U0000270F \U0001F3B5' + track['name'] + ' ' +
                                u'\U0001F919 \U0001F399' + track['artists'][0]['name'])
                    search_list.append(info_text)
            elif 'artist' in type_:
                for artist in info['artists']['items']:
                    uri_list.append(artist['uri'])
                    info_text = u'\U0001F919 \U0001F399'  + artist['name']
                    search_list.append(info_text)
            elif 'album' in type_:
                for album in info['albums']['items']:
                    uri_list.append(album['uri'])
                    info_text = (u'\U0001F3B6 \U0001F4BF' + album['name'] + ' ' +
                                u'\U0001F919 \U0001F399' + album['artists'][0]['name'])
                    search_list.append(info_text)
            return [search_list,uri_list]
        except:
            print('ERROR: mopidy search spotify control error')
            return [False, False]
    
    #This function only works with spotify
    def list_playlist_spotify(self):
        '''Outputs the current spotify user list of playlists'''
        try:
            uri_list = []
            playlist_list = []
            try:
                info = self.spotify.current_user_playlists()
            except:
                self.refresh_token()
                info = self.spotify.current_user_playlists()
            for playlist in info['items']:
                uri_list.append(playlist['uri'])
                info_text = u'\U0001F3A7 \U0001F4DD' + playlist['name']
                playlist_list.append(info_text)
            return [playlist_list,uri_list]
        except:
            print('ERROR: mopidy list playlist spotify control error')
            return [False, False]
    
    #This function only works with spotify         
    def tracks_spotify(self,uri):
        '''Outputs the track list of an album, playlist, or artist uri'''
        try:
            tracks_list = []
            uri_list = []
            if 'playlist' in uri:
                username = uri.split(':')[2]
                playlist_id = uri.split(':')[4]
                try:
                    info = self.spotify.user_playlist(username,playlist_id)
                except:
                    self.refresh_token()
                    info = self.spotify.user_playlist(username,playlist_id)
                for track in info['tracks']['items']:
                    info_text = u'\U0000270F \U0001F3B5' + track['track']['name']
                    tracks_list.append(info_text)
                    uri_list.append(track['track']['uri'])
            elif 'artist' in uri:
                try:
                    info = self.spotify.artist_top_tracks(uri)
                except:
                    self.refresh_token()
                    info = self.spotify.artist_top_tracks(uri)
                for track in info['tracks']:
                    info_text = u'\U0000270F \U0001F3B5' + track['name']
                    tracks_list.append(info_text)
                    uri_list.append(track['uri'])
            elif 'album' in uri:
                try:
                    info = self.spotify.album(uri)
                except:
                    self.refresh_token()
                    info = self.spotify.album(uri)
                for track in info['tracks']['items']:
                    info_text = u'\U0000270F \U0001F3B5' + track['name']
                    tracks_list.append(info_text)
                    uri_list.append(track['uri'])
            return [tracks_list,uri_list]
        except:
            print('ERROR: mopidy tracks spotify control error')
            return [False, False]

    def albums_spotify(self,uri):
        '''Outputs the album list of an artist uri'''
        try:
            album_list = []
            uri_list = []
            if 'artist' in uri:
                try:
                    info = self.spotify.artist_albums(uri)
                except:
                    self.refresh_token()
                    info = self.spotify.artist_albums(uri)
                for album in info['items']:
                    info_text = u'\U0001F3B6 \U0001F4BF' + album['name']
                    album_list.append(info_text)
                    uri_list.append(album['uri'])
            else:
                print('ERROR: Cannot search albums of a non artist uri')
            return [album_list,uri_list]
        except:
            print('ERROR: mopidy albums spotify control error')
            return [False, False]

    def get_status(self):
        '''Build the status namedtuple'''
        status_full = self.mopidy_status()
        status = namedtuple("status",' '.join([
            "mopidy_playing","playing", "song", "volume", "repeat", "random",
            "single", "consume", "artist", "song_number", "song_time",
            "song_percentage", "progress_s", "duration_s"]))
        if not status_full:
            '''Mopidy not enabled'''
            status.playing = False
            status.song = ' *!!* '
            status.artist = 'Music server off'
            status.song_number = '#0/0'
            status.song_time = '0:00/0:00'
            status.volume = 'xx'
            status.repeat = False
            status.random = False
            status.single = False
            status.consume = False
            status.song_percentage = 0
            return status
        if len(status_full.splitlines()) == 1: #Mopidy has no playback
            status = self.get_status_spotify(status)
        else:
            status.mopidy_playing = True
            for index, line in enumerate(status_full.splitlines()):
                if index == 2:
                    for section in line.split('   '):
                        if 'volume:' in section:
                            status.volume = str(self.get_volume_sys())+'%'
                        elif 'repeat' in section:
                            if 'on' in section:
                                status.repeat = True
                            else:
                                status.repeat = False
                        elif 'random' in section:
                            if 'on' in section:
                                status.random = True
                            else:
                                status.random = False
                        elif 'single' in section:
                            if 'on' in section:
                                status.single = True
                            else:
                                status.single = False
                        elif 'consume' in section:
                            if 'off' in section:
                                status.consume = False
                            else:
                                status.consume = True
                elif index == 0:
                    section = line.split('-')
                    if len(section)>1:
                        status.song = section[1].strip(' ')
                        status.artist = section[0].strip(' ')
                    else:
                        status.song = section[0].strip(' ')
                        status.artist = 'unknown'
                elif index == 1:
                    '''Remove silly blanks'''
                    sections = line.split(' ')
                    deleted = 0
                    for index, section in enumerate(sections):
                        if sections[index-deleted].strip(' ') == '':
                            del sections[index-deleted]
                            deleted += 1
                    '''Analyze line'''
                    if '[playing]' in line:
                        status.playing = True
                    else:
                        status.playing = False
                    status.song_number = sections[1]
                    status.song_time = sections[2]
                    status.song_percentage = int(
                        sections[3].strip(' ').strip('(').strip(')').strip('%'))
                    status.progress_s = (int(sections[2].split('/')[0].split(':')[0])*60
                                         +int(sections[2].split('/')[0].split(':')[1]))
                    status.duration_s = (int(sections[2].split('/')[1].split(':')[0])*60
                                         +int(sections[2].split('/')[1].split(':')[1]))
        return status

    def get_status_spotify(self,status):
        '''Returns the status of the spotify playback, called when the mopidy
           status is empty'''
        print('INFO: getting spotify playback')
        try:
            status_full = self.spotify.current_playback()
        except:
            self.refresh_token()
            status_full = self.spotify.current_playback()
        if status_full:
            status.mopidy_playing = False
            if status_full['is_playing']:
                status.playing = True
            else:
                status.playing = False
            status.song = status_full['item']['name']
            status.artist = status_full['item']['artists'][0]['name']
            status.song_number = '#'+str(status_full['item']['track_number'])+'/?'
            status.progress_s = int(int(status_full['progress_ms'])/1000)
            status.duration_s = int(int(status_full['item']['duration_ms'])/1000)
            status.song_time = (str(int(status.progress_s/60))+':'
                                +('0'+str(int(status.progress_s%60)))[-2:]
                                +'/'+str(int(status.duration_s/60))+':'
                                +('0'+str(int(status.duration_s%60)))[-2:])
            status.volume = str(self.get_volume_sys())+'%'
            if 'context' in status_full['repeat_state']:
                status.repeat = True
            else:
                status.repeat = False
            if status_full['shuffle_state']:
                status.random = True
            else:
                status.random = False
            status.single = False
            status.consume = False
            status.song_percentage = int(status.progress_s/status.duration_s*100)
        else:
            status.mopidy_playing = True
            status.playing = False
            status.song = 'No song'
            status.artist = 'No artist'
            status.song_number = '#0/0'
            status.song_time = '0:00/0:00'
            status.volume = str(self.get_volume_sys())+'%'
            status.repeat = False
            status.random = False
            status.single = False
            status.consume = False
            status.song_percentage = 0
            status.progress_s = 0
            status.duration_s = 0
        print('INFO: got spotify playback')
        return status
