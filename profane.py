#!/usr/local/bin/python3

from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from sys import argv
from scraper import get_lyrics, get_lyrics_from_url
import os

profanity = ["ass", "bitch", "shit", "fuck", "cunt", "nigga", "nigger", "faggot", "crap", "pussy", "dick", "queer","retard", "slut", "midget", "whore"]
sensitive = ["hell"]

#does not at ALL handle scunthorping
def check_lyrics(file=None, url=None, artist="", title="", lyrics="", strict=False):
    if file:
        if file.endswith(".mp3"):
            track = ID3(file)
            if "USLT::eng" in track.keys(): lyrics = track["USLT::eng"]
            if "TPE1" in track.keys(): artist = track["TPE1"]
            if "TIT2" in track.keys(): title = track["TIT2"]
        elif file.endswith("m4a"):
            track = MP4(file)
            if "\xa9lyr" in track: lyrics = track["\xa9lyr"]
            if "\xa9ART" in track: artist = track["\xa9ART"]
            if "\xa9nam" in track: title = track["\xa9nam"]
        else:
            return False
        print(f"Checking {title.title()} by {artist.title() if artist else 'Unknown Artist'} for profanity...")
    elif url:
        print(f"Checking URL {url} for profanity...")
        lyrics = get_lyrics_from_url(url)
    elif artist and title:
        print(f"Checking {title.title()} by {artist.title()} for profanity...")
        lyrics = get_lyrics(artist, title)

    if lyrics:
        lyrics = str(lyrics.lower())
        if strict:
            for w in profanity + sensitive:
                if w in lyrics: return True
        else:
            for w in profanity:
                if w in lyrics: return True
    else:
        return False


if __name__ == "__main__":
    arg_set = {
        "strict":False,
    }
    if len(argv) == 2 and argv[1].lower() in ['-h', '-help']:
        print("HELP MESSAGE")
    else:
        for a in argv[1:]:
            arg = a.lower()
            if arg.startswith(("-f", "-p", "-file", "-path")): arg_set['file'] = arg[arg.find("=")+1:]
            elif arg.startswith(("-l", "-u", "-url", "-link")): arg_set['url'] = arg[arg.find("=")+1:]
            elif arg.startswith(("-a", "-b", "-artist", "-by")): arg_set['artist'] = arg[arg.find("=")+1:]
            elif arg.startswith(("-t", "-n", "-title", "-name")): arg_set['title'] = arg[arg.find("=")+1:]
            elif arg == "-s": arg_set['strict'] = True

        if "file" in arg_set and "url" in arg_set:
            print("Cannot have both URL and filepath as arguments!")
        elif "file" in arg_set:
            if os.path.isfile(arg_set["file"]) and arg_set['file'].endswith((".mp3", ".m4a")):
                print(check_lyrics(file=arg_set['file'], strict=True if arg_set['strict'] else False))
            else:
                print("Path must be a valid mp3 or m4a file!")
        elif "url" in arg_set:
            print(check_lyrics(url=arg_set['url'],
                               strict=True if arg_set['strict'] else False,
                               artist=arg_set["artist"] if "artist" in arg_set else None,
                               title=arg_set['title'] if 'title' in arg_set else None))
        elif "artist" in arg_set and "title" in arg_set:
            print(check_lyrics(artist=arg_set['artist'], title=arg_set['title'], strict=True if arg_set['strict'] else False))
        else:
            print("Must have a filepath, URL, or artist & title as arguments!")