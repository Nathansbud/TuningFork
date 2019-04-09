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
            for i in range(0, len(elem)): #not a python programmer, sue me
                if elem[i].tag == "key":
                    c[elem[i].text] = elem[i+1].text
            if "Play Count" not in c:
                c["Play Count"] = "0"
            if "Podcast" not in c:
                arr.append(c)

    sort_arr(arr, method)
    return arr

def sort_arr(l, method="Play Count"):
    if method in numerical:
        l.sort(key=lambda r: int(r[method]))
    else:
        l.sort(key=lambda r: r[method])
