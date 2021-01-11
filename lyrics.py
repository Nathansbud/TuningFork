import argparse
import webbrowser

from scraper import get_lyrics, make_genius_url
from utilities import get_current_track

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("title", nargs="?", default=None)
    parser.add_argument("artist", nargs="?", default=None)
    
    parser.add_argument('-o', '--open', action='store_true')

    args = parser.parse_args()
    artist, title = args.artist, args.title
    if not (artist and title):
        curr = get_current_track()
        if not curr: 
            print("No song is playing!")
        else:
            artist, title = curr.get('artist'), curr.get('title')
    
    fellback = False
    lyrics = get_lyrics(artist, title) 
    if not lyrics:
        lyrics, fellback = get_lyrics(title, artist), True   #fallback on flipping in case I forget they order they should go in (lul)

    if lyrics:
        if not args.open: print(f"[{artist} - {title}]", lyrics.strip(), sep='\n')
        else:
            if not fellback: webbrowser.open(make_genius_url(artist, title))
            else: webbrowser.open(make_genius_url(title, artist))    
