from utilities import call_applescript, get_token

import time
import sys
import argparse

def enqueue(song, artist=None, times=1, last=None):
    spotify = get_token()
    track_uris = []
    
    if song: 
        if artist:
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}%20artist:{artist}&type=track&limit=1&offset=0").json()
        else: 
            st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}&type=track&limit=1&offset=0").json()

        track_uris = [st['tracks']['items'][0]['uri']] if st['tracks']['items'] else []
    
    elif not last:
        current = spotify.get("https://api.spotify.com/v1/me/player/currently-playing").json()
        track_uris = [current.get('item', {}).get('uri')]
    else:
        previous = spotify.get(f"https://api.spotify.com/v1/me/player/recently-played?limit={last}").json()
        track_uris = [s.get('track', {}).get('uri') for s in previous.get('items')][::-1]

    if track_uris:
        for i in range(times):  
           for uri in track_uris:
               spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={uri}")
        
        if last:
            print(f"Added{' ' + str(last) if last > 1 else ''} last played item{'s' if last > 1 else ''} to queue {times}x!")
        elif not song:
            print(f"Added currently playing track to queue {times}x!")
        else:
            print(f"Added {song.strip()} to queue {times}x!")

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
        parser.add_argument('-p', '--previous', default=0, type=int)

        args = parser.parse_args()
        enqueue(args.title, args.artist, args.times, args.previous)



if __name__ == '__main__':
    queue_track('cli')
    #queue_track('dialog' if not sys.argv[1:] else 'cli')