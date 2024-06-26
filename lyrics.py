import argparse
import tempfile
import webbrowser

from itertools import permutations

from scraper import get_lyrics, get_song_url, get_album_tracklist, get_album_url
from utilities import (
    remove_remaster,
    bold, magenta, cyan, yellow, green
)

from network import client as spotify

def track_lyrics(track, clean=True):    
    lyrics = get_lyrics(track.artist, remove_remaster(track.name) if clean else track.name)
    if lyrics: 
        return {
            "artist": track.artist,
            "album": track.album.name,
            "title": track.name,
            "lyrics": lyrics
        }
    else:
        for p in permutations(track.artist.split(", ")):
            lyrics = get_lyrics(" and ".join(p), remove_remaster(curr.get('name')) if clean else curr.get('name'))
            if lyrics:
                return {
                    "artist": " and ".join(p),
                    "album": track.album.name,
                    "title": track.name, 
                    "lyrics": lyrics
                }

        return {
            "artist": track.artist,
            "album": track.album.name,
            "title": track.name, 
            "lyrics": None
        }

def get_album_lyrics():
    tracks = spotify.get_album(spotify.get_current_track().album.id).tracks
    lyric_tracks = [track_lyrics(t) for t in tracks]
    
    joined = [
        f"[{green(t['artist'])} - {yellow(t['title'])}]\n" + 
        ("\n".join([bold(l) if l.startswith('[') else l for l in t['lyrics'].strip().split('\n')]) if t['lyrics'] else "No lyrics found :(")
        for t in lyric_tracks 
    ]

    temp_files = []
    
    for fmted in joined:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(bytes(fmted, 'utf-8'))
        temp.close()
        temp_files.append(temp.name)

    return temp_files
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artist", nargs="?", default=None)
    parser.add_argument("title", nargs="?", default=None)
    
    parser.add_argument('-o', '--open', action='store_true')
    parser.add_argument('-a', '--album', action='store_true')
    parser.add_argument('-l', '--tracklist', action='store_true')
    parser.add_argument('-n', '--noremove', action='store_true')

    args = parser.parse_args()
    
    album = None
    artist, title, tracklist = args.artist, args.title, args.tracklist
    existing_lyrics = None
    if not (artist and title):
        curr = track_lyrics(spotify.get_current_track())
        if not curr: 
            print("No song playing!") 
            exit(-1)
        else:
            if not curr.get('lyrics') and not args.tracklist: 
                pass
                
            artist, title, album, existing_lyrics = curr.get('artist'), curr.get('title'), curr.get('album'), curr.get('lyrics')
    
    fellback = False
    if tracklist:
        if not album: album = title
        if not args.noremove:
            album = remove_remaster(album)
        
        tracks = get_album_tracklist(artist, album) 
        if not tracks: 
            tracks, fellback = get_album_tracklist(album, artist), True
        
        if tracks: 
            if not args.open: 
                print(f"[{f'{cyan(album)} - {yellow(artist)}' if not fellback else f'{cyan(artist)} - {yellow(album)}'} {bold('Tracklist')}]")
                for i, track in enumerate(tracks, start=1): 
                    print(f'{magenta(i)}. {green(track)}')
            else:
                if not fellback: webbrowser.open(get_album_url(artist, album))
                else: webbrowser.open(get_album_url(album, artist))    
        else:
            print("Could not locate track list!")
        
        exit(-1)

    else:
        if not args.album:
            track = title if args.noremove else remove_remaster(title)
            
            lyrics = get_lyrics(artist, track) if not existing_lyrics else existing_lyrics
            if not (lyrics or existing_lyrics):
                lyrics, fellback = get_lyrics(track, artist), True   #fallback on flipping in case I forget they order they should go in (lul)

            if lyrics:
                if not args.open: 
                    header = f"[{green(track if not fellback else artist)} - {yellow(artist if not fellback else track)}]\n"
                    body = '\n'.join([bold(l) if l.startswith('[') else l for l in lyrics.strip().split('\n')])
                    fmted = header + body

                    temp = tempfile.NamedTemporaryFile(delete=False)
                    temp.write(bytes(fmted, 'utf-8'))
                    temp.close()

                    print(temp.name)
                else:
                    if not fellback: webbrowser.open(get_song_url(artist, track))
                    else: webbrowser.open(get_song_url(track, artist))
                    exit(-1)
            else:
                print("No lyrics found!")
                exit(-1)
        else:
            print(" ".join(get_album_lyrics()))
