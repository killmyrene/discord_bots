import datetime
import os
from datetime import datetime, timezone, date
from math import ceil
from .dataIO import dataIO
import collections

def check_folders():
    paths = ("data/ef_invade", "data/ef_invade/files")
    for path in paths:
        if not os.path.exists(path):
            print("Creating {} folder...".format(path))
            os.makedirs(path)

def get_invade_setting_filepath():
    return "data/ef_invade/settings.json"

def check_files():
    f = get_invade_setting_filepath()
    if not dataIO.is_valid_json(f):
        print("Creating {}...".format(f))
        dataIO.save_json(f, {'dummy_server_id' : generate_default_invade_priority_settings()})

def generate_default_invade_priority_settings():
    return { '0' : [], '1' : [], '2' : [], '3' :[], 'board' :[]}

def is_enchant_lvl_valid(self, enchant_lvl):
    enchant_lvl_int = int(enchant_lvl)
    if enchant_lvl_int < 0 or enchant_lvl_int > 3:
        return False
    return True