import argparse
import json

from network import client as spotify
from preferences import playlist_preference, prefs

def sort_backlog_by_album_length(playlist_id, backlog_id):
    backlog = spotify.get_playlist_tracks(playlist_id=backlog_id)
    ordered = sorted([
        (item, spotify.get_album(album_id=item.album.id).duration) 
        for item in backlog
    ], key=lambda v: v[1])
    
    spotify.replace_all_playlist_tracks(
        playlist_id, 
        [pair[0] for pair in ordered]
    )

def find_prunable_albums(backlog_id):
    backlog = spotify.get_playlist_tracks(playlist_id=backlog_id)
    albums = spotify.get_library_albums()
    
    return set(
        (t.album.name, t.album.artist) 
        for t in backlog
    ) & set(
        (a.name, a.artist)
        for a in albums
    )

def update_musook_form(form_hook, playlist_id):
    tracks = spotify.get_playlist_tracks(playlist_id=playlist_id)
    albums = list(set(f"{t.album.artist} – {t.album.name}" for t in tracks))
    spotify.post(form_hook, data=json.dumps({
        "albums": albums
    }))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"Task Manager")
    parser.add_argument("--musook", action='store_true')
    parser.add_argument("--backlog", action='store_true')
    parser.add_argument("--prune", action='store_true')
    
    args = parser.parse_args()
    solo_enabled = any([v[1] for v in args._get_kwargs()])

    should = lambda v: not solo_enabled or v

    if should(args.musook):
        print("Updating Musook form...")
        update_musook_form(
            prefs.get("MUSOOK_WEBHOOK"),
            playlist_preference("MUSOOK")
        )
    
    if should(args.backlog):
        print("Updated sorted backlog...")
        sort_backlog_by_album_length(
            playlist_preference("ORDERED"),
            playlist_preference("BACKLOG")
        )
    
    if should(args.prune):
        print("Finding backlog duplicates...")
        print(
            find_prunable_albums(playlist_preference("BACKLOG"))
        )
