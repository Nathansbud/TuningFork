from migrator import get_token
from utilities import call_applescript

import time
import sys


def enqueue(song, artist=None):
    spotify = get_token()
    if artist:
        st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}%20artist:{artist}&type=track&limit=1&offset=0").json()
    else: 
        st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}&type=track&limit=1&offset=0").json()

    track_uri = st['tracks']['items'][0]['uri'] if st['tracks']['items'] else ""
    
    spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}")
    print("Added track to queue!")


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
        enqueue(*sys.argv[1:])

if __name__ == '__main__':
    queue_track('dialog' if not sys.argv[1:] else 'cli')