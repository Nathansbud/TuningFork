import xml.etree.ElementTree as ET


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

def sort_arr(l, method="Play Count"):
    if method in numerical:
        l.sort(key=lambda r: int(r[method]))
    else:
        l.sort(key=lambda r: r[method])
