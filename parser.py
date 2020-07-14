import xml.etree.ElementTree as ET
import subprocess
import os
import json


numerical = [
    "Play Count"
]

def parse_itunes_xml(path="/Users/zackamiton/Music/iTunes/iTunes Library.xml"):
    tree = ET.parse(path)
    root = tree.getroot()
    track_list = root[0][13] #if shit goes south it's probably the fault of this line

    arr = []
    for elem in track_list:
        c = {}

        if elem.tag == "dict":
            for i in range(0, len(elem)):
                if elem[i].tag == "key":
                    c[elem[i].text] = elem[i+1].text
            if "Play Count" not in c:
                c["Play Count"] = "0"
            if "Podcast" not in c:
                arr.append(c)
    return arr

def get_tracks(playlist="Vocal"):
    tracks, error = subprocess.Popen(os.path.join(os.path.dirname(__file__), "reader", "TuneSwiftly") + (f' "{playlist}"' if playlist else ""), shell=True, stdout=subprocess.PIPE).communicate()
    items = tracks.decode('utf-8').split("\n")

    arr = []
    i = 0
    while i < len(items) - 1:
        name = items[i]
        i+=1
        artist = items[i]
        i+=1
        location = items[i]
        i+=1
        # plays = items[i]
        # i+=1

        arr.append({
            "Artist":artist,
            "Name":name,
            "Location":location
            # "Plays":plays
        })

    return arr

def get_action_items():
    with open(os.path.join(os.path.dirname(__file__), "data", "log.txt"), 'r+') as rf:
        action_list = [json.loads(l) for l in rf.readlines()]
    play_list = [item for item in action_list if "play_count" in item]
    skip_list = [item for item in action_list if "skip_count" in item]

    return play_list, skip_list


def sort_arr(l, method="Play Count"):
    if method in numerical:
        l.sort(key=lambda r: int(r[method]))
    else:
        l.sort(key=lambda r: r[method])
