from datetime import datetime
from typing import List, Optional
from utilities import green, time_progress, yellow, cyan

class AlbumObject:
    name: str
    artist: str
    uri: str
    id: str
    released: str

    tracks: Optional[List['TrackObject']]
    duration: Optional[int]
    
    def __init__(
        self,
        name=None, 
        artist=None, 
        uri=None, 
        id=None,
        released=None,
        tracks=None, 
        duration=None
    ):
        self.name = name
        self.artist = artist
        self.uri = uri
        self.id = id
        self.released = released

        self.set_tracks(tracks, duration)

    def set_tracks(self, tracks, duration=None):
        self.tracks = tracks
        self.duration = duration if duration else (
            sum(t.duration for t in tracks) if tracks else 0
        )

    def prettify(self): 
        return f"{cyan(self.name)} by {yellow(self.artist)}"

    def __str__(self):
        return f"[A]: {self.name} by {self.artist}"

class SavedAlbumObject(AlbumObject):
    added: datetime

    def __init__(self, added=None, **kwargs):
        super().__init__(**kwargs)
        self.added = added
    
    def prettify(self) -> str:
        return super().prettify()

    def __str__(self):
        return f"[@A]: {self.name} by {self.artist}"

class TrackObject:
    name: str
    artist: str
    uri: str
    id: str

    album: AlbumObject
    
    local: bool
    duration: int

    def __init__(
        self, 
        name=None, 
        artist=None, 
        uri=None, 
        id=None,
        album=None,
        local=None,
        duration=None
    ):
        self.name = name
        self.artist = artist
        self.uri = uri
        self.id = id
        self.album = album
        self.local = local
        self.duration = duration
    
    def prettify(self, album=False) -> str:
        if not album:
            return f"{green(self.name)} by {yellow(self.artist)}"
        else:
            return f"{green(self.name)} by {yellow(self.artist)} ({cyan(self.album.name)})"

    def __str__(self):
        return f"[T]: {self.name} by {self.artist}"

    def __repr__(self):
        return str(self)
    
    def __hash__(self):
        return hash(str(self))

class ActiveTrackObject(TrackObject):
    progress: int

    def __init__(self, progress=None, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
    
    def prettify(self, album=False, timestamp=False) -> str:
        base = f"{super().prettify(album=album)}"
        return base if not timestamp else f"{base} {time_progress(self.progress, self.duration, True)}"

    def __str__(self):
        return f"[@T]: {self.name} by {self.artist} (@ {self.progress})"

class PlaylistObject:
    name: str
    id: str
    uri: str

    snapshot: str
    tracks: Optional[List[TrackObject]]
    
    def __init__(
        self, 
        name=None,
        id=None,
        uri=None,
        snapshot=None,
        tracks=None
    ):
        self.name = name
        self.id = id
        self.uri = uri
        self.snapshot = snapshot
        self.tracks = tracks
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        return f"[P]: {self.name}"

def create_track_object(track_json: dict, album=None) -> TrackObject:
    track_album = album if album else (
        create_album_object(track_json.get('album')) 
        if track_json.get('album') else None
    ) 

    return TrackObject(
        name=track_json.get('name'),
        artist=', '.join(artist.get('name') for artist in track_json.get('artists', [])),
        uri=track_json.get('uri'),
        id=track_json.get('id'),
        album=track_album,
        local=track_json.get('is_local', False),
        duration=track_json.get('duration_ms')
    )

def create_active_track_object(active_track_json: dict) -> ActiveTrackObject:
    track_object = create_track_object(active_track_json.get("item"))
    return ActiveTrackObject(
        progress=active_track_json.get("progress_ms"),
        **track_object.__dict__
    )

def create_album_object(album_json: dict) -> AlbumObject:
    alb = AlbumObject(
        name=album_json.get("name"),
        artist=', '.join(artist.get('name') for artist in album_json.get('artists', [])),
        uri=album_json.get("uri"),
        id=album_json.get('id'),
        released=album_json.get("release_date")
    )

    if 'tracks' in album_json:
        album_tracks = [
            create_track_object(t, alb)
            for t in album_json['tracks']['items']
        ]

        alb.set_tracks(album_tracks)
    
    return alb

def create_saved_album_object(saved_album_json: dict) -> SavedAlbumObject:
    album_object = create_album_object(saved_album_json.get("album"))
    return SavedAlbumObject(
        added=datetime.fromisoformat(saved_album_json['added_at'][:-1]),
        **album_object.__dict__
    )

def create_playlist_object(playlist_json: dict, tracks=None) -> PlaylistObject:    
    return PlaylistObject(
        name=playlist_json.get("name"),
        snapshot=playlist_json.get("snapshot_id"),
        id=playlist_json.get("id"),
        uri=playlist_json.get("uri"),
        tracks=tracks
    )
