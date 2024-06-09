from typing import List

from utilities import green, time_progress, yellow, cyan

class AlbumObject:
    name: str
    artist: str
    uri: str
    tracks: List['TrackObject']
    
    def __init__(self, name=None, artist=None, uri=None, tracks=None):
        self.name = name
        self.artist = artist
        self.uri = uri

        self.tracks = tracks

    def prettify(self): 
        pass

class TrackObject:
    name: str
    artist: str
    uri: str
    album: AlbumObject
    
    duration: int

    def __init__(
        self, 
        name=None, 
        artist=None, 
        uri=None, 
        album=None,
        duration=None
    ):
        self.name = name
        self.artist = artist
        self.uri = uri
        self.album = album
        self.duration = duration
    
    def prettify(self, album=False) -> str:
        if not album:
            return f"{green(self.name)} by {yellow(self.artist)}"
        else:
            return f"{green(self.name)} by {yellow(self.artist)} ({cyan(self.album.name)})"
    
class ActiveTrackObject(TrackObject):
    progress: int
    local: bool

    def __init__(self, progress=None, local=None, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.local=local
    
    def prettify(self, album=False, timestamp=True):
        base = f"{super().prettify(album=album)}"
        return base if not timestamp else f"{base} {time_progress(self.progress, self.duration, True)}"

def create_track_object(track_json: dict) -> TrackObject:
    return TrackObject(
        name=track_json.get('name'),
        artist=', '.join(artist.get('name') for artist in track_json.get('artists', [])),
        uri=track_json.get('uri'),
        album=create_album_object(track_json.get('album')),
        duration=track_json.get('duration_ms')
    )

def create_active_track_object(active_track_json: dict) -> ActiveTrackObject:
    track_object = create_track_object(active_track_json.get("item"))
    
    return ActiveTrackObject(
        progress=active_track_json.get("progress_ms"),
        local=active_track_json.get("is_local"),
        **track_object.__dict__
    )

def create_album_object(album_json: dict) -> AlbumObject:
    return AlbumObject(
        name="dab dab dab"
    )

if __name__ == "__main__":
    create_active_track_object(
        
    )