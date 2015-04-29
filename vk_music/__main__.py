#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import argparse
from subprocess import call

from .vk_music import VkMusic
from .exceptions import AlreadyRunningError
from .storage import CachedProgressStorage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', type=str, nargs='?', help="Directory for synchronization")
    parser.add_argument("-uid", type=int, default=60411837, help="Vk user id")  # Default is my VK id :-)
    parser.add_argument("-token", type=str, help="access token to use")
    parser.add_argument("-token_dir", type=str, help="Directory where script will save token and temp data")
    parser.add_argument("-f", dest='force', default=False, action='store_true', help="Ignore already running error")
    parser.add_argument("-from", type=int, default=0, help="Start downloading from position")
    parser.add_argument("-to", type=int, help="End downloading on position")
    parser.add_argument("-redirect_url", type=str, help="Redirect url after getting token")
    args = vars(parser.parse_args())

    # Don't let not passed arguments to be
    for k, v in args.items():
        if v is None:
            del args[k]

    # Application ID from VK. ou can leave it as is
    args['client_id'] = 2970439

    DIR = args.get('dir', '').decode('utf-8') or os.getcwd() + '/Music'
    try:
        #Try to create directory if not exists
        if not os.path.isdir(DIR):
            os.makedirs(DIR)

        # Need write access to that dir
        os.chmod(DIR, 0o755)
        if not os.access(DIR, os.W_OK):
            raise Exception('Permission denied for dir %s' % DIR)
    except Exception as e:
        exit("Problem with directory '%s': %s" % (DIR, e))

    storage = CachedProgressStorage(DIR)
    try:
        with VkMusic(storage, **args) as manager:
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
        
if __name__ == '__main__':
    main()
