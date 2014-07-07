#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
# import atexit
import argparse
from subprocess import call

from .vk_music import VkMusic
from .exceptions import AlreadyRunningError
from .storage import ProgressStorage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', type=str, nargs='?', help="Directory for sync")
    parser.add_argument("-token", type=str, help="access token")
    parser.add_argument("-f", dest='force', default=False, action='store_true', help="Ignore already running error")
    parser.add_argument("-from", type=int, help="Start downloading from position")
    parser.add_argument("-to", type=int, help="End on position")
    parser.add_argument("-token_file", type=str, help="File for storing access token")
    parser.add_argument("-uid", type=int, help="Vk user id")
    args = parser.parse_args()

    # print(args.dir.decode('utf-8'))
    #exit()

    DIR = args.dir and args.dir.decode('utf-8') or os.getcwd() + '/Music'
    try:
        #Try to create directory if not exists
        if not os.path.isdir(DIR):
            os.makedirs(DIR)

        # Need write access to that dir
        os.chmod(DIR, 0777)
        if not os.access(DIR, os.W_OK):
            raise Exception('Permission denied for dir %s' % DIR)
    except Exception as e:
        exit("Problem with directory '%s': %s" % (DIR, e))

    manager_kwargs = {
        'force': args.force
    }

    if getattr(args, 'from', None):
        manager_kwargs['from'] = getattr(args, 'from', None)

    if args.to:
        manager_kwargs['to'] = args.to

    if args.token:
        manager_kwargs['token'] = args.token

    storage = ProgressStorage(DIR)
    try:
        with VkMusic(storage, client_id=2970439, uid=60411837, **manager_kwargs) as manager:
            # Start working
            result = manager.synchronize()
            try:
                call(['notify-send',
                      'Vk Music',
                      'Saved: %(saved)s\n'
                      'Skipped: %(skipped)s\n'
                      'Removed: %(removed)s\n'
                      'Not removed: %(not_removed)s' % result])
            except Exception:
                pass
    except AlreadyRunningError:
        # If is running - terminate
        print('Other sync process is running. Please wait')