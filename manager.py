from network import client as spotify
from preferences import playlist_preference

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

if __name__ == "__main__":
    sort_backlog_by_album_length(
       playlist_preference("DUMMY_2"),
       playlist_preference("BACKLOG")
    )