from utilities import green, time_progress, yellow, cyan

class AlbumObject:
    name: str
    artist: str
    uri: str
    id: str
    
    def __init__(
        self,
        name=None, 
        artist=None, 
        uri=None, 
        id=None, 
    ):
        self.name = name
        self.artist = artist
        self.uri = uri
        self.id = id

    def prettify(self): 
        return f"{cyan(self.name)} by {yellow(self.artist)}"

    def __str__(self):
        return f"[A]: {self.name} by {self.artist}"

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

class ActiveTrackObject(TrackObject):
    progress: int

    def __init__(self, progress=None, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
    
    def prettify(self, album=False, timestamp=True) -> str:
        base = f"{super().prettify(album=album)}"
        return base if not timestamp else f"{base} {time_progress(self.progress, self.duration, True)}"

    def __str__(self):
        return f"[@T]: {self.name} by {self.artist} (@ {self.progress})"

def create_track_object(track_json: dict, album=None) -> TrackObject:
    track_album = album if album else (
        create_album_object(track_json.get('album')) 
        if track_json.get('album') else None
    ) 

    return TrackObject(
        name=track_json.get('name'),
        artist=', '.join(artist.get('name') for artist in track_json.get('artists', [])),
        uri=track_json.get('uri'),
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
    return AlbumObject(
        name=album_json.get("name"),
        artist=', '.join(artist.get('name') for artist in album_json.get('artists', [])),
        uri=album_json.get("uri"),
        id=album_json.get('id')
    )