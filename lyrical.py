from parser import parse_itunes_xml

from scraper import path_prettify
from scraper import get_lyrics_from_url
from scraper import get_lyrics

from mutagen.id3 import ID3
from random import randint

def lyrics_from_itunes():
    arr = parse_itunes_xml()
    lyrics = []

    for x in arr:
        if "Vocal" in x["Comments"] and x["Location"].endswith("mp3"):
            lyrics.append(x)

    song_choice = lyrics[randint(0, lyrics.__len__())]
    print(song_choice["Name"] + " by " + song_choice["Artist"])

    lyrics_arr = str(ID3(path_prettify(song_choice["Location"]))["USLT::eng"]).split("\n")
    lyrics_formatted = []

    for l in lyrics_arr:
        if l.__len__() > 0 and l[0] == "[":
            pass
        else:
            lyrics_formatted.append(l)
    return lyrics_formatted

def lyrics_from_itunes_with_fields(artist, name):
    found = False
    for x in parse_itunes_xml():
        if artist == x["Artist"] and name == x["Name"] and x["Location"].endswith("mp3"):
           found = True
           print(name + " by " + artist)
           song = ID3(path_prettify(x["Location"]))

           if "USLT::eng" in song.keys():
               lyrics_arr = str(song["USLT::eng"]).split("\n")
               lyrics_formatted = []
               for l in lyrics_arr:
                   if l.__len__() > 0 and l[0] == "[":
                       pass
                   else:
                       lyrics_formatted.append(l)
               return lyrics_formatted
           else:
               print("Song has no lyrics!")
        else:
            pass
    if not found:
        print(name + " by " + artist + " does not exist in library!")

def lyrics_from_genius_by_artist(artist, name):
    return [line for line in get_lyrics(artist, name).split("\n") if not line.startswith("[")]

def lyrics_from_genius_by_url(url):
    return [line for line in get_lyrics_from_url(url).split("\n") if not line.startswith("[")]

def show_lyrics(lyrics, line_num=5):
    if line_num >= lyrics.__len__():
        return lyrics
    else:
        if line_num > -1:
            lb = randint(0, lyrics.__len__() - 1 - line_num) #lower bound
            ub = lb + line_num
        else:
            lb = randint(0, lyrics.__len__() - 2)  # lower bound
            ub = randint(lb + 1, lyrics.__len__() - 1)
        lyrics_snippet = lyrics[lb : ub]

        while lyrics_snippet.__len__() - lyrics_snippet.count("") != line_num:
            if ub < (lyrics.__len__() - 1): ub+=1
            elif lb > 0: lb -=1
            else: break

            lyrics_snippet = lyrics[lb : ub]

        return lyrics_snippet

if __name__ == "__main__":
    pass
