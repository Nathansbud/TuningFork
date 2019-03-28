from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen import MutagenError

from parser import parse_itunes_xml

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

def get_lyrics(artist, name, file, rewrite=False):
    artist = artist.split(" ft. ")[0].lower().replace(" ", "-").capitalize().replace("•", "").replace("!", "-").replace("(", "").replace(")", "").replace("é", "e").replace(".", "").replace("í", "i").replace(",", "").replace("&", "and")
    name = name.lower().replace(" – ", "-").replace(" ", "-").replace(".", "").replace("!", "").replace("'", "").replace("/", "-").replace(",", "").replace("?", "").replace("(", "").replace(")", "").replace("’", "").replace(":", "").replace("&", "and")

    song_tags = ID3(file) #call mutagen file

    if not rewrite:
        if "USLT::eng" in song_tags.keys():
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
    except TypeError:
        print("Song add failed! Genius link was " + lyrics_url)
    except MutagenError:
        print("Song add failed! Genius link was " + lyrics_url)
    except ID3NoHeaderError:
        print("Cannot add lyrics to an m4a! Genius link was " + lyrics_url)

def add_all_lyrics(rewrite=False):
    for s in arr:
        if "Comments" in s:
            if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3") and "Imbecile" not in s["Comments"]:
                try:
                    get_lyrics(s["Artist"], s["Name"], s["Location"][7:].replace("%20", " ").replace("%E2%80%A2", "•").replace("%E2%80%93", "–").replace("e%CC%81", "é").replace("i%CC%81", "í").replace("%23", "#"), rewrite)#[7:] to counter file:// at start, %20 replace with spaces
                except: #Bad exception handling technique but it be like that sometimes!!!!
                    print("Song add failed (in add all)! Song was " + s["Name"] + " by " + s["Artist"])
    print("Done!")

if __name__ == "__main__":
    add_all_lyrics()
    pass