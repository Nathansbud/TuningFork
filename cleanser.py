from mutagen.id3 import ID3
import os
from sys import argv

def cleanse_directory(dirname=None, extra_tags=None):
    """
    Tags:
        - TALB: Album Name
        - TSO2: Album Artist
        - TPE1: Artist
        - TRCK: Track Number
        - APIC: Picture
        - COMM::eng: iTunes Comment
        - TIT2: Title
        - USLT: Lyrics
        - TCON: Genre
        - TPOS: Disk #
        - TSSE: Encoding
        - TDRC: Recording Date
    """
    accepted_tags = ["TSOP", "TALB", "TPE1", "TPE2", "TRCK", "APIC", "APIC:", "COMM::eng", "TIT2", "USLT::eng", "TCON", "TPOS", "TSSE", "TDRC"]
    if extra_tags: accepted_tags += extra_tags
    files = list(filter(lambda e: e != ".DS_Store", os.listdir(dirname)))
    for track in files:
        #td - flac/m4a
        if track.lower().endswith(".mp3"):
            file = ID3(os.path.join(dirname, track))
            remove_tags = set()
            for tag in file.keys():
                if not tag in accepted_tags:
                    remove_tags.add(tag)
            for remove in remove_tags:
                file.delall(remove)
            file.save()

def cleanse_all(accepted_tags=None):
    p = "/Users/zackamiton/Music/iTunes/iTunes Media/Music"
    for music_dir in directory_filter(p):
        for album_dir in directory_filter(os.path.join(p, music_dir)):
            cleanse_directory(os.path.join(p, music_dir, album_dir), accepted_tags)

def directory_filter(l): return filter(lambda fi: os.path.isdir(os.path.join(l, fi)), os.listdir(l))
def ds_filter(l): return filter(lambda e: e != ".DS_Store", os.listdir(l))

if __name__ == "__main__":
    if len(argv) == 1: cleanse_all()
    elif len(argv) >= 2:
        if argv[1].lower() == "-h" or argv[1].lower() == "-help":
            print("Usage:\tcleaner [directory] [tags ...]: Removes unwanted ID3 tags from files in a directory")
            print("\t[path]: Directory to remove (taken as Music directory if omitted)")
            print("\t[tags ...]: Additional ID3 tags to keep")
        elif os.path.isdir(argv[1]):
            cleanse_directory(argv[1], argv[1:])
        else:
            print(f"Error on '{argv[1]}', argument 1 must be a filepath (-h for help)")