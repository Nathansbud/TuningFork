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
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

###ENDS HERE—THANK YOU TO

##To-do: Try-catch block in case genius page doesn't exist (so it doesn't crash the ones that do) with a log file, output lyrics to text files using itunes filepath
##also how to deal with features? Genius scraping won't work with them...
def get_lyrics(artist, name, file):
    print("Adding lyrics to " + name + " by " + artist)

    artist = artist.lower().replace(" ", "-").capitalize().replace("•", "").replace("!", "-").replace("(", "").replace(")", "").replace("é", "e").replace(".", "").replace("í", "i").replace(",", "").replace("&", "and")
    name = name.lower().replace(" - ", "-").replace(" ", "-").replace(".", "").replace("!", "").replace("'", "").replace("/", "-").replace(",", "").replace("?", "").replace("(", "").replace(")", "").replace("’", "").replace(":", "")

    song_tags = ID3(file) #call mutagen file
    lyrics_url = "https://genius.com/" + artist + "-" +  name + "-lyrics"

    try:
        raw_html = simple_get(lyrics_url)

        soup = BeautifulSoup(raw_html, 'html.parser')
        soup.prettify()

        lyrics = (soup.find(class_="lyrics")).text
        lyrics = lyrics[2:len(lyrics)-2] #always seems to have the same number of leading/trailing newlines...could fix if not working right, but seems to based on 5 dif songs

        # print(song_tags.keys())
        song_tags.delall("USLT") #Delete lyric tags if they already exist (might be a bad move, but I don't use lyrics enough to care)
        song_tags[u"USLT::eng"] = (USLT(encoding=3, lang=u'eng', text=lyrics)) #Write USLT tag
        song_tags.save() #
    except TypeError as TE:
        print("Song add failed! Genius link was " + lyrics_url)
    except MutagenError as ME:
        print("Song add failed! Genius link was " + lyrics_url)
    except ID3NoHeaderError as HE:
        print("Cannot add lyrics to an m4a! Genius link was " + lyrics_url)



def add_all_lyrics():
    for s in arr:
        if "Comments" in s:
            if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3"):
                try:
                    get_lyrics(s["Artist"], s["Name"], s["Location"][7:].replace("%20", " ").replace("%E2%80%A2", "•").replace("%E2%80%93", "–").replace("e%CC%81", "é").replace("i%CC%81", "í").replace("%23", "#"))#[7:] to counter file:// at start, %20 replace with spaces
                except: #Bad exception handling techniques but it be like that sometimes
                    print("Song add failed (in add all)! Song was " + s["Name"] + " by " + s["Artist"])

if __name__ == "__main__":
    add_all_lyrics()
    pass