import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

import unidecode
import re

###CODE THAT IS NOT MINE STARTS HERE:
def simple_get(url):
    try:
        with closing(requests.get(url, stream=True)) as resp:
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

def genius_clean(field):
    #unidecode turns • into *...annoying.
    field = unidecode.unidecode(field.lower().split("(feat. ")[0].split( " ft. ")[0].split( " feat. ")[0].split(" featuring. ")[0].split("  feat. ")[0].split(" (with ")[0].replace("&", "and").replace("•", "").replace("æ", "").replace("œ", "").replace("’", "")) #split off featuring, replace & with and
    field = re.sub(r"(?<=\s)[^a-z0-9](?=\s)", "-", field) #replace space-surrounded punctuation with hyphen
    field = re.sub(r"(?<=[a-z0-9])[^a-z0-9\.\'\’\'](?=[a-z0-9])", "-", field).replace(" - ", "-").replace(" ", "-") #replace mid-string punctuation; i.e. "P!nk"
    return re.sub(r"[^a-z0-9\-]", "", field)

def get_song_url(artist, name):
    artist = genius_clean(artist).capitalize()
    name = genius_clean(name).rstrip("-")
    return "https://genius.com/" + artist + "-" + name + "-lyrics"

def get_album_url(artist, name):
    artist = genius_clean(artist).capitalize().rstrip('-')
    album = genius_clean(name).capitalize().rstrip('-')

    return f"https://genius.com/albums/{artist}/{album}"

def get_album_tracks(artist, name):
    url = get_album_url(artist, name)
    resp = requests.get(url)

    if resp.status_code == 404: return []
    else: 
        try:
            page = BeautifulSoup(resp.text, 'html.parser')
            return [track.text.strip()[:-1*len('Lyrics')].strip() for track in page.findAll('h3', {'class': 'chart_row-content-title'})]
        except Exception as e:
            print(e)
  
def get_lyrics(artist, name):
    return get_lyrics_from_url(get_song_url(artist, name))

def get_lyrics_from_url(url, surpress=True):
    try:
        raw_html = simple_get(url)
        soup = BeautifulSoup(raw_html, 'html.parser')
        container = soup.select('[data-lyrics-container]')
        
        text_collection = []
        for c in container:
            for br in c('br'):
                br.replace_with('\n')
            
            text_collection.append(c.text)
                
        return "\n".join(text_collection)
    except TypeError:
        if not surpress: print(f"Get lyrics failed on URL '{url}'")
        return False

if __name__ == "__main__":
    pass
    
    


