#!/usr/local/bin/python3.7

import difflib
import shutil
import os
import json

music_dir = "/Users/zackamiton/Music/iTunes/"

main_name = 'iTunes Library.xml'
temp_name = 'Temp Library.xml'
old_name = 'Compare.xml'

keys = {
    "date":{
        "start":"<key>Date</key><date>",
        "end":"</date>"
    },
    "play_count":{
        "start":"<key>Play Count</key><integer>",
        "end":"</integer>"
    },
    "play_date":{
        "start":"<key>Play Date</key><integer>",
        "end":"</integer>"
    },
    "track_id":{
        "start":"<key>Track ID</key><integer>",
        "end":"</integer>"
    },
    "name":{
        "start":"<key>Name</key><string>",
        "end":"</string>"
    },
    "artist":{
        "start":"<key>Artist</key><string>",
        "end":"</string>"
    },
    "play_date_utc":{
        "start":"<key>Play Date UTC</key><date>",
        "end":"</date>"
    },
    "skip_count":{
        "start":"<key>Skip Count</key><integer>",
        "end":"</integer>"
     },
    "skip_date":{
        "start":"<key>Skip Date</key><date>",
        "end":"</date>"
    }
}

def strip_fields(string, field):
    if field in keys:
        return string.strip()[len(keys[field]['start']):-len(keys[field]['end'])].replace("~", "-") #using tilde as delimiter
    return string

def ssw(string, field): #strip startswith, friggin tabs
    if field in keys:
        return string.strip().startswith(keys[field]['start'])
    return string.strip().startswith(field)

def match_for(strlist, matches, start_point):
    return_keys = {}
    while not ssw(strlist[start_point], "<dict>"):
        start_point -= 1

    while not ssw(strlist[start_point], "</dict>"):
        start_point += 1
        for key in matches:
            if ssw(strlist[start_point], key):
                return_keys[key] = strip_fields(new[start_point], key)
                break
    return return_keys

with open(music_dir + main_name) as lib, open(music_dir + old_name) as comp:
    new = lib.readlines()
    comp = comp.readlines()

changed_index = 0
change_zone = False
change_set = []

for line in difflib.context_diff(new, comp, fromfile=music_dir + 'iTunes Library.xml', tofile=music_dir+'Compare.xml'):
    line = line.strip()
    if line.startswith("*** ") and line.endswith("****"):
        changed_index = int(line[4:line.find(",")])+1
        change_zone = True
    elif line.startswith("---") and line.endswith("----"):
        changed_index = 0
        change_zone = False

    if change_zone:
        if line.startswith("!"):
            changed_index += 1
            line = line[1:]
            if ssw(line, "date"):
                print(strip_fields(line, "date"))
            elif ssw(line, "play_count"):
                get_keys = match_for(new, ["track_id", "name", "artist", "play_date_utc", "play_count"], changed_index)
                change_set.append(get_keys)
            elif ssw(line, "skip_count"):
                get_keys = match_for(new, ["track_id", "name", "artist", "skip_count", "skip_date"], changed_index)
                change_set.append(get_keys)
            else:
                pass
                # print(line)

with open(os.path.dirname(__file__) + os.sep + "data" + os.sep + "log.txt", 'a+') as lf:
    for line in change_set:
        lf.write(json.dumps(line) + "\n")

shutil.copyfile(music_dir + main_name, music_dir + temp_name)
shutil.copyfile(music_dir + temp_name, music_dir + old_name)

if __name__ == '__main__':
    pass
