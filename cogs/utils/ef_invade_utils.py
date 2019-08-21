import datetime
import os
from datetime import datetime, timezone, date
from math import ceil
from .dataIO import dataIO
import collections

import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

def import_googleapi():

    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    filepath = get_invade_import_api_filepath()
    filepath = "secret_file.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(filepath, scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("Copy of Legislators 2017").sheet1

    # Extract and print all of the values
    list_of_hashes = sheet.get_all_records()
    print(list_of_hashes)

def get_num_stars(score:int, is_enchanted=False):
    numStars = 0

    if score > 600:
        numStars += 1

    if score > 540:
        numStars += 1

    if score > 450:
        numStars += 1

    if score > 380:
        numStars += 1

    if score > 300:
        numStars += 1

    if is_enchanted and numStars > 0:
        return 1

    return numStars


