import xml.etree.ElementTree as ET

tree = ET.parse("/Users/zackamiton/Music/iTunes/iTunes Library.xml")
root = tree.getroot()
track_list = root[0][15]

def parse_itunes_xml():
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

    arr.sort(key=lambda r: int(r["Play Count"]))
    # for a in arr:
    #     print(a["Name"] + ": " + a["Play Count"])

    return arr



if __name__ == "__main__":
    pass