from bs4 import BeautifulSoup
import requests
import re
from utilities import get_vocal_paths
from mutagen.id3 import ID3
from mutagen.mp4 import MP4

pronouns = [['he', 'his'], ['she', 'her'], ['they', 'their']]
tracks = get_vocal_paths()
checked = {}
def check_track(path):
    if path.endswith("mp3"):
        track = ID3(path)
        artist = str(track['TPE1'] if 'TPE1' in track else track['TPE2'])
    elif path.endswith("m4a"):
        track = MP4(path)
        artist = str(track['©ART'][0])
    else:
        return
    if not artist in checked:
        print(f"Checking {artist}...")
        page = BeautifulSoup(requests.get(f"https://en.wikipedia.org/wiki/{artist}").content, 'html.parser').find("body")
        if len(page.find_all(class_="noarticletext")) == 0:
            page_text = str(page)
            male_match = re.findall(f"(?i)\\b({'|'.join(pronouns[0])})\\b", page_text)
            female_match = re.findall(f"(?i)\\b({'|'.join(pronouns[1])})\\b", page_text)
            enby_match = re.findall(f"(?i)\\b({'|'.join(pronouns[2])})\\b", page_text)
            checked[artist] = {"M":len(male_match), "F":len(female_match), "T":len(enby_match)}
        else:
            print(f"No data for {artist}!")
    else:
        print(f"{artist} already checked, {checked[artist]}")

for track in tracks: check_track(track)