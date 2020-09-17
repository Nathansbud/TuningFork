#!/Users/zackamiton/Code/TuningFork/venv/bin/python
from migrator import get_token
from utilities import call_applescript
import time

def enqueue():
    song_dialog = """    
    set songToQueue to ""
    tell application "System Events"
	    set songToQueue to text returned of (display dialog "Input Track:" default answer "" with title "Add to Queue")
    end tell
    songToQueue
    """

    #Not Working
    # open_spotify = """
    # if application "Spotify" is not running
    #     tell application "Spotify"
    #         play
    #         set priorVolume to sound volume as text
    #         set pv to priorVolume
    #         set sound volume to 0
    #         "RAN"
    #     end tell
    # end if
    # """
    #
    # reset_volume_and_skip = """
    # tell application "Spotify"
    #     set sound volume to 100
    # end tell
    # """

    song_input = call_applescript(song_dialog)['output'].strip()
    if song_input:
        # conditional_open = call_applescript(open_spotify)['output'].strip()
        # if conditional_open: time.sleep(2)
        song, *artist = song_input.lower().split(" by ")
        spotify = get_token()
        if song and artist: st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}%20artist:{artist[0]}&type=track&limit=1&offset=0").json()
        else: st = spotify.get(f"https://api.spotify.com/v1/search/?q={song}&type=track&limit=1&offset=0").json()

        track_uri = st['tracks']['items'][0]['uri'] if st['tracks']['items'] else ""
        print(spotify.post(f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}"))
        # if conditional_open: call_applescript(reset_volume_and_skip.replace("[VOLUME]", conditional_open))


if __name__ == '__main__':
    enqueue()