import xml.etree.ElementTree as ET
from urllib import parse


numerical = [
    "Play Count"
]

def parse_itunes_xml(path="/Users/zackamiton/Music/iTunes/iTunes Library.xml", method="Play Count"):
    tree = ET.parse(path)
    root = tree.getroot()
    track_list = root[0][15]  # p sure this doesn't always work oops

    arr = []
    for elem in track_list:
        c = {}

        if elem.tag == "dict":
            for i in range(0, len(elem)): #not a python programmer, sue me (okay i might, this can just be elem, not my problem rn tho will do later)
                if elem[i].tag == "key":
                    c[elem[i].text] = elem[i+1].text
            if "Play Count" not in c:
                c["Play Count"] = "0"
            if "Podcast" not in c:
                arr.append(c)

    sort_arr(arr, method)
    return arr

##KEEPING THIS AS A TALE FOR FUTURE ME
#SON. Google before doing.
# - iTunes Library XML (as SHOULD have been clear from the fact that it is GENERATED) is NOT the file iTunes Data is read from in-app.
# - Its role is to provide stupid developers (such as yourself) DATA but NOT A MEANS TO EDIT ITUNES DATA
# - Editing FILES THEMSELVES works as it's actually editing the underlying files by adding ID3/MP4 tags
# - iTunes Metadata (plays, ratings, ...) is stored in the .itl file which is NOT editable; AppleScripts can do it, Python not sure
# TL;DR writing to the iTunes XML does NOTHING.

# def get_elem():
#     loc = "/Users/zackamiton/Music/iTunes/iTunes Media/Music/Tears For Fears/The Hurting/02 Mad World.mp3"
#     count = 5
#     tree = ET.parse("/Users/zackamiton/Music/iTunes/iTunes Library.xml")
#     root = tree.getroot()
#     track_list = root[0][15]  # p sure this doesn't always work oops
#
#     for s in track_list:
#         if s.tag == "dict":
#             if path_prettify(s[-1].text) == loc:
#                 song = list(s)
#                 for t in range(len(song)):
#                     # print(t)
#                     if song[t].text == "Play Count":
#                         print(song[t+1].text)
#                         song[t+1].text = str(count)
#     tree.write("/Users/zackamiton/Music/iTunes/iTunes Library.xml")

# def path_prettify(path): #yes, this is in scraper, idk how to deal with circular dependencies SHUT UP
#     if path.startswith("file:///"):
#         return parse.unquote(path[7:])
#     return parse.unquote(path)

def sort_arr(l, method="Play Count"):
    if method in numerical:
        l.sort(key=lambda r: int(r[method]))
    else:
        l.sort(key=lambda r: r[method])