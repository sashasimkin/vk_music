#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import atexit

from vk_music import VkMusic

if __name__ == '__main__':
    DIR = sys.argv[1] if len(sys.argv) > 1 else os.getcwd() + '/Music'
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

    manager = VkMusic(
        cwd=DIR,
        client_id=2970439,  # VK Application id, you can use this
        uid=60411837  # Your VK-id
    )

    #If script not running - register safe exit with cleanup
    if not manager.is_running():
        atexit.register(lambda: manager.exit('Exited', silent=True))

    manager.synchronize()
