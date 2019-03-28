#!/usr/local/opt/python/bin/python3.7

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen import MutagenError

from parser import parse_itunes_xml
import unidecode

import os

arr = parse_itunes_xml()

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

##To-do: Try-catch block in case genius page doesn't exist (so it doesn't crash the ones that do) with a log file, output lyrics to text files using itunes filepath
##also how to deal with features? Genius scraping won't work with them...

def has_lyrics(file):
    return "USLT::eng" in ID3(file).keys()

def get_lyrics(artist, name, file, rewrite=False):
    song = name
    by = artist

    artist = unidecode.unidecode(artist.split(" ft. ")[0].split(" feat. ")[0].lower().replace(" ", "-").capitalize().replace("•", "").replace("!", "-").replace("(", "").replace(")", "").replace("é", "e").replace(".", "").replace("í", "i").replace(",", "").replace("&", "and"))
    name = unidecode.unidecode(name.lower().replace(" – ", "-").replace(" / ", "/").replace(" ~ ", "-").replace(" ", "-").replace(".", "").replace("!", "").replace("'", "").replace("/", "-").replace(",", "").replace("?", "").replace("(", "").replace(")", "").replace("’", "").replace(":", "").replace("&", "and").replace("[", "").replace("]", ""))

    song_tags = ID3(file) #call mutagen file

    if not rewrite:
        if has_lyrics(file):
            return

    lyrics_url = "https://genius.com/" + artist + "-" +  name + "-lyrics"

    try:
        raw_html = simple_get(lyrics_url)

        soup = BeautifulSoup(raw_html, 'html.parser')
        soup.prettify()

        lyrics = (soup.find(class_="lyrics")).text #Genius has all lyric data in a div with class lyrics, text gets plaintext
        lyrics = lyrics[2:len(lyrics)-2] #Delete trailing and leading newlines
        song_tags.delall("USLT")
        song_tags[u"USLT::eng"] = USLT(encoding=3, lang=u'eng', text=lyrics) #Write USLT tag
        song_tags.save() #
        print("Lyrics added to " + song + " by " + by)
    except TypeError:
        print("Song add failed! Genius link was " + lyrics_url)
    except MutagenError:
        print("Song add failed! Genius link was " + lyrics_url)
    except ID3NoHeaderError:
        print("Cannot add lyrics to an m4a! Genius link was " + lyrics_url)

def add_lyrics(track, rewrite=False):
    try:
        get_lyrics(track["Artist"], track["Name"], file_path_prettify(track["Location"]), rewrite)  # [7:] to counter file:// at start, %20 replace with spaces
    except MutagenError:
        print("Lyric add failed, likely due to error in system file path! File path is " + track["Location"])

def file_path_prettify(path):
    return path[7:].replace("%20", " ").replace("%E2%80%A2", "•").replace("%E2%80%93", "–").replace("e%CC%81","é").replace("i%CC%81", "í").replace("%23", "#").replace("%C3%A9", "é").replace("%5B", "[").replace("%5D", "]").replace("%E2%98%86", "☆")

def add_all_lyrics(rewrite=False):
    for s in arr:
        if "Comments" in s:
            if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3") and "Imbecile" not in s["Comments"]:
                add_lyrics(s, rewrite)
    print("Done!")

if __name__ == "__main__":
    add_all_lyrics(False)
    pass