#!/usr/local/opt/python/bin/python3.7
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen import MutagenError

from urllib import parse

from parser import parse_itunes_xml, get_vocal_tracks
import unidecode
import re

from tkinter.filedialog import askopenfilename, Tk, askopenfilenames

###CODE THAT IS NOT MINE STARTS HERE:
def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        return None

def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return resp.status_code == 200 and content_type is not None and content_type.find('html') > -1
###ENDS HERE—THANK YOU TO https://realpython.com/python-web-scraping-practical-introduction/

def has_lyrics(file):
    if file.endswith(".mp3"):
        return "USLT::eng" in ID3(file).keys()
    else:
        return "\xa9lyr" in MP4(file).keys()

def genius_clean(field):
    #unidecode turns • into *...annoying.
    field = unidecode.unidecode(field.split( " ft. ")[0].split( " feat. ")[0].split(" featuring. ")[0].split("  feat. ")[0].split(" (with ")[0].replace("&", "and").replace("•", "")) #split off featuring, replace & with and
    field = re.sub("(?<=\s)[^a-zA-Z0-9](?=\s)", "-", field) #replace space-surrounded punctuation with hyphen
    field = re.sub("(?<=[a-zA-Z0-9])[^a-zA-Z0-9'.](?=[a-zA-Z0-9])", "-", field).replace(" - ", "-").replace(" ", "-") #replace mid-string punctuation; i.e. "P!nk"
    return re.sub("[^a-zA-Z0-9\-]", "", field).lower()

def make_genius_url(artist, name):
    artist = genius_clean(artist).capitalize()
    name = genius_clean(name).rstrip("-")
    return "https://genius.com/" + artist + "-" + name + "-lyrics"

def get_lyrics(artist, name):
    return get_lyrics_from_url(make_genius_url(artist, name))

def get_lyrics_from_url(url):
    try:
        raw_html = simple_get(url)

        soup = BeautifulSoup(raw_html, 'html.parser')
        lyrics = (soup.find(class_="lyrics")).text #Genius has all lyric data in a div with class lyrics, text gets plaintext
        lyrics = lyrics[2:len(lyrics)-2] #Delete trailing and leading newlines
        return lyrics
    except TypeError:
        print(f"Get lyrics failed on URL '{url}'")
        return False

def write_lyrics(artist, name, file, rewrite=False):
    song = name
    by = artist

    try:
        if file.endswith(".mp3"): #should reduce these checks
            song_tags = ID3(file) #ID3 unique to MP3s, other a/v types use MP4 specifications on tagging
        else:
            song_tags = MP4(file)

        if not rewrite:
            if has_lyrics(file):
                return

        lyrics = get_lyrics(artist, name)

        if lyrics is not None:
            if file.endswith(".mp3"):
                song_tags.delall("USLT")
                song_tags[u"USLT::eng"] = USLT(encoding=3, lang=u'eng', text=lyrics) #Lyric tag
                song_tags.save()
            else:
                song_tags["\xa9lyr"] = lyrics
                song_tags.save()
            print("Lyrics added to " + song + " by " + by)
    except TypeError:
        print("Lyric add failed in WL (TypeError)!")
    except MutagenError:
        print("Lyric add failed in WL (MutagenError)!  File extension was " + file)
    except ID3NoHeaderError:
        print("Lyric add failed in WL (ID3NoHeader)! File extension was " + file)

def write_lyrics_with_path(path, rewrite): #Attempted re-write of write_lyrics() using just path argument;
    try:
        if path.endswith(".mp3"):  # should reduce these checks
            song_tags = ID3(path)  # ID3 unique to MP3s, other a/v types use MP4 specifications on tagging
            if "TPE2" in song_tags:
                artist = str(song_tags["TPE2"])
            else:
                artist = str(song_tags["TPE1"])
            name = str(song_tags["TIT2"])
        else:
            song_tags = MP4(path)
            artist = str(song_tags["\xa9ART"])
            name = str(song_tags["\xa9nam"])

        write_lyrics(artist, name, path, rewrite)
    except TypeError:
        print("Lyric add failed in WLWP (TypeError)! " + path)
    except MutagenError:
        print("Lyric add failed in WLWP (MutagenError)!  File extension was " + path)
    except ID3NoHeaderError:
        print("Lyric add failed in WLWP (ID3NoHeader)! File extension was " + path)


def add_lyrics(track, rewrite=False):
    try:
        write_lyrics(track["Artist"], track["Name"], path_prettify(track["Location"]), rewrite)
    except MutagenError:
        print("Lyric add failed, likely due to error in system file path! File path is " + track["Location"])

def path_prettify(path):
    if path.startswith("file:///"):
        return parse.unquote(path[7:])
    return parse.unquote(path)

def add_all_lyrics(rewrite=False, use_xml=False):
    if use_xml:
        for s in parse_itunes_xml():
            if "Comments" in s:
                if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3") and "Imbecile" not in s["Comments"]:
                    add_lyrics(s, rewrite)
    else:
        for s in get_vocal_tracks():
            add_lyrics(s, rewrite)
    print("Done!")

def write_tracklist():
    root = Tk()
    root.withdraw()
    files = askopenfilenames(parent=root, title="Choose Tracks")
    tracklist = root.tk.splitlist(files)
    for to_write in tracklist:
        write_lyrics_with_path(to_write, True)
    print("Done!")

if __name__ == "__main__":
    add_all_lyrics()
    pass