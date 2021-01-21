from migrator import get_token
from utilities import call_applescript

import time
import sys
import argparse

def enqueue(song, artist=None, times=1):
    spotify = get_token()
    track_uri =  ''
    if song: 
        if artist:
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}%20artist:{artist}&type=track&limit=1&offset=0").json()
        else: 
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}&type=track&limit=1&offset=0").json()

        track_uri = st['tracks']['items'][0]['uri'] if st['tracks']['items'] else ""
    else:
        current = spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json()
        track_uri = current.get('item', {}).get('uri')

    if track_uri:
        for i in range(times):  
           spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}")
        print(f"Added {'currently playing track' if not song else song.strip()} to queue ({times}T)!")

def queue_track(mode='dialog'):
    if mode == 'dialog':
        song_dialog = """    
        set songToQueue to ""
        tell application "System Events"
            set songToQueue to text returned of (display dialog "Input Track:" default answer "" with title "Add to Queue")
        end tell
        songToQueue
        """

        song_input = call_applescript(song_dialog)['output'].strip()
        if song_input:
            song, *artist = song_input.lower().split(" by ")
            enqueue(song, artist)
    
    elif 'cli':
        parser = argparse.ArgumentParser(description="Spotify track queuer")

        parser.add_argument('title', nargs='?', default=None)
        parser.add_argument('artist', nargs='?', default=None)
        parser.add_argument('-t', '--times', default=1, type=int)

        args = parser.parse_args()
        enqueue(args.title, args.artist, args.times)

if __name__ == '__main__':
    queue_track('cli')
    #queue_track('dialog' if not sys.argv[1:] else 'cli')