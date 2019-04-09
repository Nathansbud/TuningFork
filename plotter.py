from parser import parse_itunes_xml
import matplotlib.pyplot as plt
import numpy as np
import math

plt.style.use("seaborn")

def artist_plot():
    art = parse_itunes_xml("Artist")
    artists = {}
    for val in art:
        if val["Artist"] in artists:
            artists[val["Artist"]] += 1
        else:
            artists[val["Artist"]] = 1

    sorted_artists = sorted(artists.items(), key=lambda v: int(v[1]), reverse=True)
    print(sorted_artists)


def play_plot():
    arr = parse_itunes_xml("Play Count")

    l = [int(x["Play Count"]) for x in arr]

    print(l)

    val_list = []
    freq_list = []

    count = 1

    for val in range(1, len(l)):
        if l[val] != l[val - 1] or val == len(l) - 1:
            print(str(l[val - 1]) + ": " + str(count))
            val_list.append(l[val - 1])
            freq_list.append(count)
            count = 1
            # if val == len(l) - 1 and l[val] != l[val - 1]:
            #     print(str(l[val]) + ": " + str(count))
            #     val_list.append(l[val])
            #     freq_list.append(count)

            # just horrible code but it's 11:42 and my brain is asleep, fix this off more elegantly by one later
            #also commented because I know the last song is bonetrousle and a huge outlier; handle this better later, see ^
        else:
            count+=1

    plt.scatter(val_list, freq_list)
    plt.show()

if __name__ == "__main__":
    play_plot()
    pass
