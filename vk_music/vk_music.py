# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import Counter
import os
import json

from .utils import prnt, replace_chars
from .exceptions import *
from .consts import SAVED, SKIPPED
from datetime import datetime

from six.moves import input as read_input
from six.moves import urllib


class Song(object):
    """
    Just wrapper for interactions with storage

    As functionality extending shown black_list feature
    """

    def __init__(self, storage, song=None, *args, **kwargs):
        """
        Init object
        Prepare song name as self.name

        @param storage: Song storage
        @param song: Dict with artist, title and url fields or only name
        @param args:
        @param kwargs:
        @raise RuntimeError:
        """
        self.storage = storage
        self.manager = kwargs.get('manager', None)

        #Process song dict to class props
        try:
            self.name = song.get('name', None) or ('%s - %s.mp3' % (song['artist'].strip(), song['title'].strip()))
            self.name = replace_chars(self.name, ('/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', ';', '!'))
            self.name = os.path.normpath(self.name)
        except KeyError:
            # self.name = replace_chars(self.name, ('/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.', ';', '!'))
            RuntimeError('For creation "Song" object you must provide '
                         '{dict}"song" argument with name or artist and title')

        self.url = song.get('url', None)

    def out(self, *args, **kwargs):
        if self.manager:
            self.manager.out(*args, **kwargs)

    def save(self, **kwargs):
        """
        Save song
        Download from self.url and save to self.path with self.name
        """
        if not hasattr(self, 'url'):
            raise RuntimeError('Can not load song')

        # r means remote file
        r = urllib.request.urlopen(self.url)

        # Such kind of manipulation need in case of errors and broken files later
        return self.storage.write(self.name, r, number=kwargs.get('number', None))

    def remove(self):
        """
        Remove file
        """
        self.storage.remove(self.name)

    def in_blacklist(self):
        """
        Check for song must be downloaded and saved
        returns True/False as Yes/Not
        """
        return self.name.strip()[-8:-4] == r'-bl-'


class VkMusic(object):
    song_class = Song

    def __init__(self, storage, *args, **kwargs):
        """
        song_class=Song

        Updates self.SETTINGS from kwargs
        """
        self.storage = storage
        self.SETTINGS = {
            'client_id': None,
            'uid': None,
            'gid': None,
            'from': 0,
            'to': None,
            'token_dir': '~/.vk-music',
            'redirect_url': 'https://sima.pro/public/token.html'
        }
        self.SETTINGS.update(kwargs)
        # Process ~ inside path and create directory for data
        self.SETTINGS['token_dir'] = os.path.expanduser(self.SETTINGS['token_dir'])
        try:
            os.makedirs(self.SETTINGS['token_dir'])
        except OSError as e:
            if e.errno != 17:
                self.exit('Can\'t create data directory: %s' % e)

        if (not self.SETTINGS['uid'] and not self.SETTINGS['gid']) or not self.SETTINGS['client_id']:
            raise ValueError('You must provide client_id and uid or gid')

    def __enter__(self):
        if self.storage.exists('.lock') and not self.SETTINGS.get('force', False):
            raise AlreadyRunningError()
        else:
            self.storage.touch('.lock')
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        try:
            self.storage.remove('.lock')
        except Exception as e:
            print('Error in exit: %s' % e)

        if exc_type:
            self.out(exc_type, exc_val, exc_tb)

    def get_api_url(self):
        """
        Get URL for api requests
        """
        try:
            token = self.get_token()
        except Exception as e:
            self.exit('Problems within getting token: %s' % e)

        url = 'https://api.vk.com/method/audio.get.json?uid=%s&access_token=%s'\
              %\
              (self.SETTINGS['uid'], token)

        if self.SETTINGS['gid']:
            url += '&gid=' + self.SETTINGS['gid']

        return url

    @property
    def token_file(self):
        return os.path.join(self.SETTINGS['token_dir'], 'token.txt')

    def clear_token(self):
        os.remove(self.token_file)

    def store_token(self, token):
        open(self.token_file, 'w').write(token)

    def get_token(self, force_new=False):
        if self.SETTINGS.get('token') and not force_new:
            return self.SETTINGS.get('token')

        try:
            token = open(self.token_file, 'r').read()
        except IOError:
            token_url = 'https://oauth.vk.com/authorize?client_id=%(client_id)s&scope=audio,offline&redirect_uri=' \
                        '%(redirect_url)s&display=page&response_type=token' % self.SETTINGS

            self.out("Open this URL in browser: %s\n"
                     "Then copy token from url: " % token_url, end="")

            token = read_input()
            self.store_token(token)

        return token

    def get_songs(self):
        """
        Get songs to be downloaded
        """
        s_from = self.SETTINGS['from']
        s_to = self.SETTINGS['to']
        while True:
            songs = json.loads(urllib.request.urlopen(self.get_api_url()).read())
            try:
                songs['count'] = len(songs['response'])
                songs['response'] = songs['response'][s_from:s_to]
                break
            except KeyError:
                # Clear old token and get new
                self.clear_token()
                self.get_token(force_new=True)

        return songs

    def synchronize(self):
        """
        Main function, that does the job according configuration
        e.g:
        obj = VkMusic()
        obj.synchronize()
        """
        stats = Counter()
        self.out('Fetching music list...')

        songs = self.get_songs()

        to_sync = {
            'new': [],
            'old': self.storage.files_list()
        }

        self.out('Starting download list to "%s"...' % self.storage.get_id())

        status_stats = {
            SAVED: 'saved',
            SKIPPED: 'skipped'
        }
        i = 0
        for song_info in songs['response']:
            song = self.song_class(self.storage, song_info)

            if song.in_blacklist():
                continue
            else:
                to_sync['new'].append(song.name)

            try:
                status = song.save(number=i)
                stats[status_stats[status]] += 1
            except (OSError, urllib.error.HTTPError) as e:
                self.out("Error %d: %s, %s" % (i, song.name, str(e)))
            i += 1

        if self.SETTINGS['from'] == 0 and self.SETTINGS['to'] is None:
            to_remove = list(set(to_sync['old']) - set(to_sync['new']))
            for i, f in enumerate(to_remove, 1):
                try:
                    Song(self.storage, {'name': f}).remove()
                    stats['removed'] += 1
                    self.out("%s. Removed %s" % (i, f))
                except OSError as e:
                    stats['not_removed'] += 1
                    self.out("%s. Error while removing %s, exc_info: %s" % (i, f, e))

        self.out('That is all. Enjoy.')

        return stats

    # Helper functions
    @staticmethod
    def out(*args, **kwargs):
        return prnt('[{}]'.format(datetime.now().isoformat()), *args, **kwargs)

    def exit(self, *args, **kwargs):
        self.__exit__()
        self.out(*args, **kwargs)

        return exit()