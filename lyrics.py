import argparse
import webbrowser

from scraper import get_lyrics, get_song_url, get_album_tracks, get_album_url
from utilities import get_current_track

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("title", nargs="?", default=None)
    parser.add_argument("artist", nargs="?", default=None)
    
    parser.add_argument('-o', '--open', action='store_true')
    parser.add_argument('-a', '--album', action='store_true')

    args = parser.parse_args()
    
    album = None
    artist, title, album_flag = args.artist, args.title, args.album
    if not (artist and title):
        curr = get_current_track()
        if not curr: 
            print("No song is playing!")
        else:
            artist, title, album = curr.get('artist'), curr.get('title'), curr.get('album')
    
    fellback = False
    if album_flag:
        if not album: album = title
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
        lyrics = get_lyrics(artist, title) 
        if not lyrics:
            lyrics, fellback = get_lyrics(title, artist), True   #fallback on flipping in case I forget they order they should go in (lul)

        if lyrics:
            if not args.open: print(f"[{artist if not fellback else title} - {title if not fellback else artist}]", lyrics.strip(), sep='\n')
            else:
                if not fellback: webbrowser.open(get_song_url(artist, title))
                else: webbrowser.open(get_song_url(title, artist))   