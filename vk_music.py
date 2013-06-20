#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import urllib2
import json
import tempfile


class Song(object):
    def __init__(self, workdir, song=None, song_name=None, *args, **kwargs):
        """
        Init object, check workdir for existing and save to self.path
        Prepare song name as self.name
        """
        if not os.path.isdir(workdir):
            raise OSError('Directory "%s" does not exist' % workdir)

        self.path = workdir
        #Process song dict to class props
        if song is not None:
            #File name
            self.name = ('%s - %s.mp3' % (song['artist'].strip(), song['title'].strip()))
            #Download url
            self.url = song['url']
            #Working directory
        elif song_name is not None:
            self.name = song_name
        else:
            raise RuntimeError('For creation "Song" object you must provide "song" or "song_name" argument')

        self.name = self.replace_chars(self.name, ('/', '\\', '"', '?', '!', ':', ';', '<', '>'))
        self.name = os.path.normpath(self.name)

    def save(self):
        """
        Save song
        Download from self.url and save to self.path with self.name
        """
        if not hasattr(self, 'url'):
            raise RuntimeError('Can not load song')

        fc = urllib2.urlopen(self.url).read()

        f = open(os.path.join(self.path, self.name), 'wb+')
        f.write(fc)
        f.close()

    def remove(self):
        """
        Remove file
        """
        try:
            os.remove(os.path.join(self.path, self.name))
            return True
        except (WindowsError, OSError):
            return False

    def is_exist(self):
        """
        Is file exist in passed path
        """
        return os.path.isfile(os.path.join(self.path, self.name))

    def is_valid(self):
        """
        Check for song must be downloaded and saved
        returns True/False as Yes/Not
        """
        return self.name.strip()[-8:-4] != r'-bl-'

    def replace_chars(self, string, chars, char=''):
        for to_replace in chars:
            string = string.replace(to_replace, char)
        return string


class VkMusic(object):
    SETTINGS = {
        #Vk settings
        'client_id': None,
        'uid': None,
        'gid': None,
        'song_class': Song,
        #Fs settings
        'cwd': None,
        'lock': os.path.join('%(cwd)s', '.lock')
    }

    def __init__(self, *args, **kwargs):
        """
        song_class=Song

        Updates self.SETTINGS from kwargs
        """
        self.SETTINGS.update(kwargs)

        if (not self.SETTINGS['uid'] and not self.SETTINGS['gid']) or not self.SETTINGS['client_id']:
            raise ValueError('You must provide client_id and uid or gid')

        self.initial(*args, **kwargs)

    def initial(self, *args, **kwargs):
        if 'cwd' not in kwargs:
            raise ValueError('You must provide the save to directory in kwargs as "cwd"')
        else:
            if not os.path.isdir(kwargs['cwd']):
                raise OSError('Directory "%s" does not exist' % kwargs['cwd'])

            self.SETTINGS['cwd'] = kwargs['cwd']
            self.SETTINGS['lock'] = self.SETTINGS['lock'] % self.SETTINGS

    def is_running(self):
        """
        Check if sync process in current directory running
        """
        return os.path.isfile(self.SETTINGS['lock'])

    def get_cwd(self):
        """
        Получить текущую папку для синхронизации
        """
        return self.SETTINGS['cwd']

    def get_api_url(self):
        """
        Get URL for api requests
        """
        try:
            token = self.get_token()
        except Exception, e:
            self.exit('Problems within getting token: %s' % e)

        url = 'https://api.vkontakte.ru/method/audio.get.json?uid=%s&access_token=%s'\
              %\
              (self.SETTINGS['uid'], token)

        if self.SETTINGS['gid']:
            url += '&gid=' + self.SETTINGS['gid']

        return url

    def get_token(self):
        token_file = os.path.join(tempfile.gettempdir(), 'vk_token.txt')
        try:
            token = open(token_file, 'r').read()
        except IOError:
            TOKEN_URL = 'https://oauth.vk.com/authorize?client_id=2970439&scope=audio,offline&redirect_uri=http://oauth.vk.com/blank.html&display=wap&response_type=token'

            self.out("""Токен устарел.\n
            Для получения токена - пройди по ссылке: %s'\n
            Введи значение access_token сюда: """ % TOKEN_URL,
                      end="")

            token = raw_input()
            open(token_file, 'w').write(token)

        return token

    def get_songs(self):
        songs = json.loads(urllib2.urlopen(self.get_api_url()).read())
        try:
            songs['count'] = len(songs['response'])
        except KeyError:
            self.exit('Произошла ошибка при получении токена, перезапуск скрипта должен помочь.')

        return songs

    def get_old_songs(self):
        """
        Get old songs list
        """
        return os.listdir(self.SETTINGS['cwd'])

    def synchronize(self):
        """
        Main function, that does the job according configuration
        e.g:
        music = VkMusic()
        music.synchronize()
        """
        if self.is_running():
            self.exit('Script already running.', cleanup=False)

        self.out('Fetching music list...')

        songs = self.get_songs()

        to_sync = {
            'new': [],
            'old': self.get_old_songs()
        }

        self.out('Starting download list...')

        for i, song_info in enumerate(songs['response'], 1):
            song = self.SETTINGS['song_class'](self.SETTINGS['cwd'], song_info)

            if song.is_valid():
                to_sync['new'].append(song.name)
            else:
                song.remove()

            if not (song.is_exist() or song.is_valid()):
                self.out("Skip %d: %s" % (i, song.name))
                continue

            try:
                song.save()
            except Exception, e:
                self.out("Error %d: %s, %s" % (i, song.name, str(e)))
            else:
                self.out("Saved %d: %s" % (i, song.name))

        to_remove = list(set(to_sync['old']) - set(to_sync['new']))
        for i, f in enumerate(to_remove):
            if Song(self.SETTINGS['cwd'], song_name=f).remove():
                self.out("Removed %d: (%s)" % (i, f))
            else:
                self.out("Error while removing %d: (%s), %s" % (i, f, e))

        self.exit('That is all!')

    # Helper functions
    def out(self, *args, **kwargs):
        return self.prnt(*args, **kwargs)

    def prnt(self, *args, **kwargs):
        args = list(args)
        for (i, v) in enumerate(args):
            v = str(v)
            if isinstance(v, basestring):
                try:
                    args[i] = unicode(v, "utf-8")
                except TypeError:
                    args[i] = v.encode("utf-8")

        return print(*args, **kwargs)

    def exit(self, *args, **kwargs):
        if kwargs.get('cleanup', True):
            try:
                os.remove(self.SETTINGS['lock'])
            except (OSError, KeyError):
                pass

        self.out(*args, **kwargs)
        return exit()