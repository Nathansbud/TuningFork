import argparse

from scraper import get_lyrics
from utilities import get_current_track

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("title", nargs="?", default=None)
    parser.add_argument("artist", nargs="?", default=None)

    args = parser.parse_args()
    artist, title = args.artist, args.title
    if not (artist and title):
        curr = get_current_track()
        if not curr: 
            print("No song is playing!")
        else:
            artist, title = curr.get('artist'), curr.get('title')
    
    lyrics = get_lyrics(artist, title)
    if lyrics:
        print(f"[{artist} - {title}]", lyrics.strip(), sep='\n')

