import xml.etree.ElementTree as ET
import subprocess
import os


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

def get_vocal_tracks():
    tracks, error = subprocess.Popen(os.path.dirname(__file__) + os.sep + "scripts" + os.sep + "TuneSwiftly", shell=True, stdout=subprocess.PIPE).communicate()
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

        arr.append({
            "Artist":artist,
            "Name":name,
            "Location":location
        })

    return arr

def sort_arr(l, method="Play Count"):
    if method in numerical:
        l.sort(key=lambda r: int(r[method]))
    else:
        l.sort(key=lambda r: r[method])
