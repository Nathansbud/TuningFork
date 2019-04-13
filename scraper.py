#!/usr/local/opt/python/bin/python3.7

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen import MutagenError

from urllib import parse

from parser import parse_itunes_xml
import unidecode
import re

from tkinter.filedialog import askopenfilename, Tk


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

def has_lyrics(file):
    if file.endswith(".mp3"):
        return "USLT::eng" in ID3(file).keys()
    else:
        return "\xa9lyr" in MP4(file).keys()

def genius_clean(field):
    #unidecode turns • into *...annoying.
    field = unidecode.unidecode(field.split( " ft. ")[0].split( " feat. ")[0].split(" featuring. ")[0].replace("&", "and").replace("•", "")) #split off featuring, replace & with and
    field = re.sub("(?<=\s)[^a-zA-Z0-9](?=\s)", "-", field) #replace space-surrounded punctuation with hyphen
    field = re.sub("(?<=[a-zA-Z0-9])[^a-zA-Z0-9'.](?=[a-zA-Z0-9])", "-", field).replace(" - ", "-").replace(" ", "-") #replace mid-string punctuation; i.e. "P!nk"
    return re.sub("[^a-zA-Z0-9\-]", "", field).lower()

def get_lyrics(artist, name): #too tired to do without breaking things, but restructure get_lyrics to use this and rename to write_lyrics
    artist = genius_clean(artist).capitalize()
    name = genius_clean(name)

    if name[-1] == "-":
        name = name[:-1] #not sure if necessary, to make sure it doesn't end in hyphens...should be done a tad bit more elegantly

    lyrics_url = "https://genius.com/" + artist + "-" +  name + "-lyrics"

    try:
        raw_html = simple_get(lyrics_url)

        soup = BeautifulSoup(raw_html, 'html.parser')
        soup.prettify()

        lyrics = (soup.find(class_="lyrics")).text #Genius has all lyric data in a div with class lyrics, text gets plaintext
        lyrics = lyrics[2:len(lyrics)-2] #Delete trailing and leading newlines
        return lyrics
    except TypeError:
        print("Song add failed! Genius link was " + lyrics_url)
    except MutagenError:
        print("Song add failed! Genius link was " + lyrics_url)


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
        print("Lyric add failed (TypeError)!")
    except MutagenError:
        print("Lyric add failed (MutagenError)!  File extension was " + file[file.rfind("."):])
    except ID3NoHeaderError:
        print("Lyric add failed (ID3NoHeader)! File extension was " + file[file.rfind("."):])

def add_lyrics(track, rewrite=False):
    try:
        write_lyrics(track["Artist"], track["Name"], path_prettify(track["Location"]), rewrite) #[7:] slice to counter file:// at start
    except MutagenError:
        print("Lyric add failed, likely due to error in system file path! File path is " + track["Location"])

def path_prettify(path):
    if path.startswith("file:///"):
        return parse.unquote(path[7:])
    return parse.unquote(path)

def add_all_lyrics(rewrite=False):
    for s in arr:
        if "Comments" in s:
            if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3") and "Imbecile" not in s["Comments"]:
                add_lyrics(s, rewrite)
    print("Done!")

def select_track(): #Not used rn, but called file explorer window, can be used to get filepath for track, i.e. write_lyrics("Pink Floyd", "Money", select_track(), True) and then song is selected
    Tk().withdraw()
    return askopenfilename()

if __name__ == "__main__":
    # write_lyrics("King Gizzard & The Lizard Wizard", "Wah Wah", select_track(), True)
    add_all_lyrics()
    pass
