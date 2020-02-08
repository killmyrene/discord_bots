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

def get_invade_import_api_filepath():
    return "../data/ef_invade/secret_file.json"

def check_files():
    f = get_invade_setting_filepath()
    if not dataIO.is_valid_json(f):
        print("Creating {}...".format(f))
        dataIO.save_json(f, {'dummy_server_id' : generate_default_invade_priority_settings()})

def generate_default_invade_priority_settings():
    return { '0' : [], '1' : [], '2' : [], '3' :[], 'board' :[]}

def is_enchant_lvl_valid(enchant_lvl):
    enchant_lvl_int = int(enchant_lvl)
    if enchant_lvl_int < 0 or enchant_lvl_int > 3:
        return False
    return True

def get_num_stars(score:int, is_enchanted=False):
    numStars = 0

    if score > 600:
        numStars += 1

    if score > 540:
        numStars += 1

    if score > 460:
        numStars += 1

    if score > 380:
        numStars += 1

    if score > 300:
        numStars += 1

    if is_enchanted:
        if score >= 650 or (510 <= score < 540) or (590 <= score < 600):
            return 0
        elif numStars > 0:
            return 1

    return numStars