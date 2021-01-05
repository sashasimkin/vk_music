# ***This project is unmaintained***

vk_music
========
Python package for downloading music from vk.com with ability to customize behaviour.

Installation
========
`pip install vk_music` or clone repo and run `main.py` from `vk_music`

Usage
========
There is system-wide command `vk_music`:
```
vk_music [-h] [-uid UID] [-token TOKEN] [-token_dir TOKEN_DIR] [-f]
              [-from FROM] [-to TO] [-redirect_url REDIRECT_URL]
              [dir]
```
Available options:
```
positional arguments:
  dir                   Directory for synchronization

optional arguments:
  -h, --help            show this help message and exit
  -uid UID              Vk user id
  -client_id CID              Client application id
  --threads[-t] 2       Count of threads where perform the work
  -token TOKEN          access token to use
  -token_dir TOKEN_DIR  Directory where script will save token and temp data
  -f                    Ignore already running error
  -from FROM            Start downloading from position
  -to TO                End downloading on position
  -redirect_url REDIRECT_URL
                        Redirect url after getting token
```
Also you can subclass vk_music.VkMusic and customize it for you needs.

Notes
========
* If you always receiving token request - you should obtain token from same IP address as machine you running script.
* You can see examples in defaults.py
