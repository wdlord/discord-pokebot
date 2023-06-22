# Code by https://github.com/wdlord

import os

# This exists to avoid any potential KeyErrors that would otherwise silently be raised.
TOKEN = os.environ['TOKEN']
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']

DEV_TOKEN = os.environ.get('DEV_TOKEN')
