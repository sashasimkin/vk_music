#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import atexit
import argparse

from vk_music import VkMusic

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', type=str, nargs='?', help="Directory for sync")
    parser.add_argument("-token", type=str, help="access token")
    parser.add_argument("-uid", type=int, help="Vk user id")
    args = parser.parse_args()

    #print(args.dir.decode('utf-8'))
    #exit()

    DIR = args.dir.decode('utf-8') or os.getcwd() + '/Music'
    try:
        #Try to create directory if not exists
        if not os.path.isdir(DIR):
            os.makedirs(DIR)

        # Need write access to that dir
        os.chmod(DIR, 0777)
        if not os.access(DIR, os.W_OK):
            raise Exception('Permission denied for dir %s' % DIR)
    except Exception, e:
        exit("Problem with directory '%s': %s" % (DIR, e))

    manager_kwargs = {}

    if args.token:
        manager_kwargs['token'] = args.token

    # Init manager
    manager = VkMusic(
        cwd=DIR,
        client_id=2970439,  # VK Application id, can use this
        uid=args.uid or 60411837,  # You VK-id, may be set as main.py -uid=
        **manager_kwargs
    )

    #If script not running - register safe exit with cleanup
    if not manager.is_running():
        atexit.register(lambda: manager.exit('Exited', silent=True))

    # Start all the work
    manager.synchronize()