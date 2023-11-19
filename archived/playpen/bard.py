from urllib import parse

from mutagen.id3 import ID3, USLT, ID3NoHeaderError
from mutagen.mp4 import MP4
from mutagen import MutagenError

from tkinter.filedialog import askopenfilename, Tk, askopenfilenames

from sparser import parse_itunes_xml, get_tracks
from scraper import get_lyrics

def has_lyrics(file):
    if file.endswith(".mp3"):
        return "USLT::eng" in ID3(file).keys()
    else:
        return "\xa9lyr" in MP4(file).keys()

def write_lyrics(artist, name, file, rewrite=False):
    song = name
    by = artist

    try:
        if file.endswith(".mp3"): #should reduce these checks
            song_tags = ID3(file) #ID3 unique to MP3s, other a/v types use MP4 specifications on tagging
        else:
            song_tags = MP4(file)

        if not rewrite:
            if has_lyrics(file):
                return

        lyrics = get_lyrics(artist, name)

        if lyrics is not None:
            if file.endswith(".mp3"):
                song_tags.delall("USLT")
                song_tags[u"USLT::eng"] = USLT(encoding=3, lang=u'eng', text=lyrics) #Lyric tag
                song_tags.save()
            else:
                song_tags["\xa9lyr"] = lyrics
                song_tags.save()
            print("Lyrics added to " + song + " by " + by)
    except TypeError:
        print("Lyric add failed in WL (TypeError)!")
    except MutagenError:
        print("Lyric add failed in WL (MutagenError)!  File extension was " + file)
    except ID3NoHeaderError:
        print("Lyric add failed in WL (ID3NoHeader)! File extension was " + file)

def write_lyrics_with_path(path, rewrite): #Attempted re-write of write_lyrics() using just path argument;
    try:
        if path.endswith(".mp3"):  # should reduce these checks
            song_tags = ID3(path)  # ID3 unique to MP3s, other a/v types use MP4 specifications on tagging
            if "TPE2" in song_tags:
                artist = str(song_tags["TPE2"])
            else:
                artist = str(song_tags["TPE1"])
            name = str(song_tags["TIT2"])
        else:
            song_tags = MP4(path)
            artist = str(song_tags["\xa9ART"])
            name = str(song_tags["\xa9nam"])

        write_lyrics(artist, name, path, rewrite)
    except TypeError:
        print("Lyric add failed in WLWP (TypeError)! " + path)
    except MutagenError:
        print("Lyric add failed in WLWP (MutagenError)!  File extension was " + path)
    except ID3NoHeaderError:
        print("Lyric add failed in WLWP (ID3NoHeader)! File extension was " + path)


def add_lyrics(track, rewrite=False):
    try:
        write_lyrics(track["Artist"], track["Name"], path_prettify(track["Location"]), rewrite)
    except MutagenError:
        print("Lyric add failed, likely due to error in system file path! File path is " + track["Location"])

def path_prettify(path):
    if path.startswith("file:///"):
        return parse.unquote(path[7:])
    return parse.unquote(path)

def add_all_lyrics(rewrite=False, use_xml=False):
    if use_xml:
        for s in parse_itunes_xml():
            if "Comments" in s:
                if "Vocal" in s["Comments"] and s["Location"].endswith(".mp3") and "Imbecile" not in s["Comments"]:
                    add_lyrics(s, rewrite)
    else:
        for s in get_tracks():
            add_lyrics(s, rewrite)
    print("Done!")

def write_tracklist():
    root = Tk()
    root.withdraw()
    files = askopenfilenames(parent=root, title="Choose Tracks")
    tracklist = root.tk.splitlist(files)
    for to_write in tracklist:
        write_lyrics_with_path(to_write, True)
    print("Done!")