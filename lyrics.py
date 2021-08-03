import argparse
import webbrowser
import re

from scraper import get_lyrics, get_song_url, get_album_tracks, get_album_url
from enqueue import current_lyrics

def remove_after(inp, endings=None, regex_endings=None):
    if regex_endings:
        for r in regex_endings: 
            inp = re.split(r, inp)[0]

    if endings:
        for ending in endings:
            if ending in inp: inp = inp.split(ending)[0].strip()

    return inp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artist", nargs="?", default=None)
    parser.add_argument("title", nargs="?", default=None)
    
    parser.add_argument('-o', '--open', action='store_true')
    parser.add_argument('-a', '--album', action='store_true')
    parser.add_argument('-n', '--noremove', action='store_true')

    args = parser.parse_args()
    
    album = None
    artist, title, album_flag = args.artist, args.title, args.album
    existing_lyrics = None
    if not (artist and title):
        curr = current_lyrics()
        if not curr: 
            print("No song playing!") 
            exit(0)
        else:
            if not curr.get('lyrics'): 
                print("No lyrics found!")
            artist, title, album, existing_lyrics = curr.get('artist'), curr.get('title'), curr.get('album'), curr.get('lyrics')
    
    fellback = False
    if album_flag:
        if not album: album = title
        if not args.noremove:
            album = remove_after(
                album, 
                endings=[
                    ' (Expanded', 
                    ' (Deluxe', 
                    ' (Original Mono', 
                    ' (Remastered', 
                    ' (Bonus', 
                    ' (Legacy Edition', 
                    ' (Super Deluxe Edition',
                    ' (Special Edition',
                    ' ['
                ], 
                regex_endings=[
                    r'\s\(\d{4} Remaster',
                    r'\(\d+(.*?) Anniversary(.*?)Edition'
                ]
            )
        
        tracks = get_album_tracks(artist, album) 
        if not tracks: 
            tracks, fellback = get_album_tracks(album, artist), True
        
        if tracks: 
            if not args.open: 
                print(f"[{f'{album} - {artist}' if not fellback else f'{artist} - {album}'} Tracklist]")
                for i, track in enumerate(tracks, start=1): 
                    print(f'{i}. {track}')
            else:
                if not fellback: webbrowser.open(get_album_url(artist, album))
                else: webbrowser.open(get_album_url(album, artist))    
        else:
            print("Could not locate track list!")

    else:
        track = title if args.noremove else remove_after(
            title, 
            endings=[' (i. '],
            regex_endings=[
                r'\-(\s\d{4})? Remaster'
            ]
        )
        
        lyrics = get_lyrics(artist, track) if not existing_lyrics else existing_lyrics
        if not (lyrics or existing_lyrics):
            lyrics, fellback = get_lyrics(track, artist), True   #fallback on flipping in case I forget they order they should go in (lul)

        if lyrics:
            if not args.open: print(f"[{artist if not fellback else track} - {track if not fellback else artist}]", lyrics.strip(), sep='\n')
            else:
                if not fellback: webbrowser.open(get_song_url(artist, track))
                else: webbrowser.open(get_song_url(track, artist))
        else:
            print("No lyrics found!")