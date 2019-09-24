from parser import parse_itunes_xml, get_vocal_tracks, get_action_items
import matplotlib.pyplot as plt
import datetime
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
        else:
            count+=1

    plt.scatter(val_list, freq_list)
    plt.show()

def plot_actions():
    played, skipped = get_action_items()
    played.sort(key=lambda x: datetime.datetime.strptime(x['play_date_utc'], "%Y-%m-%dT%H:%M:%SZ").timestamp() + 19800)
    skipped.sort(key=lambda x: datetime.datetime.strptime(x['skip_date'], "%Y-%m-%dT%H:%M:%SZ").timestamp() + 19800)

if __name__ == "__main__":
    plot_actions()
    pass
