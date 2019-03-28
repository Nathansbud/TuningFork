#!/usr/local/opt/python/bin/python3.7

from tune_scraper import add_lyrics
from tune_scraper import arr
import sys

if __name__ == "__main__":
    if len(sys.argv) is not 3:
        print("Call failed! Must have 2 arguments: name, artist")
    else:
        artist = sys.argv[2]
        name = sys.argv[1]
        passed = False

        for e in arr:
            if e["Artist"].lower() == artist.lower() and e["Name"].lower() == name.lower():
                add_lyrics(e, True)
                passed = True
        if not passed:
            print("This song does not exist! Arguments must be [name, artist]")
    sys.exit()



