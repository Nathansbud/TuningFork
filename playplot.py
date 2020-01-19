import json
import os
import matplotlib.pyplot as plt
from datetime import datetime, date
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
with open(os.path.join(os.path.dirname(__file__), "data", "log.txt"), "r") as lf: lines = [json.loads(l) for l in lf.readlines()]
lines.sort(key=lambda l: l['skip_date'] if 'skip_date' in l else l['play_date_utc'])

def std(date_string): return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
def track_events(name, artist): return [e for e in lines if e['name'] == name and e['artist'] == artist]
def plot_track(name, artist):
    tracks = track_events(name, artist)

    dates_play = [std(d['play_date_utc']) for d in tracks if "play_count" in d]
    dates_skip = [std(d['skip_date']) for d in tracks if "skip_count" in d]

    fig, ax = plt.subplots()

    plt.title(f"{name} by {artist}")
    plt.xticks(rotation=45)
    plt.xlabel("Time")

    ax.plot_date(dates_skip, ["Skip"]*len(dates_skip), color='b')
    ax.plot_date(dates_play, ["Play"]*len(dates_play), color='r')

    ax.set_xlim([dates_play[0] if dates_play[0] < dates_skip[0] else dates_skip[0], datetime.today()])

    plt.gcf().autofmt_xdate()
    plt.show()

plot_track("Flamingo", "Kero Kero Bonito")
plot_track("Mr. Clean", "Yung Gravy")
plot_track("What?", "A Tribe Called Quest")


def plot_tracks(*name_artist_pair):
    name_artist_pair = name_artist_pair[::-1]
    fig, ax = plt.subplots()
    plt.title("Song Comparisons")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plots = []
    colors = ['red', 'orange', '#FADA5e', 'green', 'blue', 'indigo', 'violet'][::-1]

    #Single Plot
    # for idx, pair in enumerate(name_artist_pair):
    #     tracks = track_events(pair[0], pair[1])
    #     dates_play = [std(d['play_date_utc']) for d in tracks if "play_count" in d]
    #     dates_skip = [std(d['skip_date']) for d in tracks if "skip_count" in d]
    #     plots.append(ax.plot_date(dates_skip, ["Skip"]*len(dates_skip), color=colors[idx]))
    #     plots.append(ax.plot_date(dates_play, ["Play"]*len(dates_play), color=colors[idx]))

    #Stacked Plot
    for idx, pair in enumerate(name_artist_pair):
        tracks = track_events(pair[0], pair[1])
        plays = [std(d['play_date_utc']) for d in tracks if "play_count" in d]
        plots.append(ax.plot_date(plays, [pair[0]]*len(plays), color=colors[idx]))

    ax.set_xlim(right=datetime.today())
    # plt.legend((p[0] for p in plots), (f"{n[0]} by {n[1]}" for n in name_artist_pair), loc="upper left", bbox_to_anchor=(1,1), prop={'size': 6})
    plt.gcf().autofmt_xdate()
    plt.show()
    fig.savefig(os.path.join(os.path.dirname(__file__), "graphs", "song_comparisons.png"))


plot_tracks(
    ("Cooks", "Still Woozy"),
    ("What?", "A Tribe Called Quest"),
    ("Mr. Clean", "Yung Gravy"),
    ("Yonkers", "Tyler, the Creator"),
    ("Won't Trade", "Q-Tip"),
    ("Truth Hurts", "Lizzo"),
    ("Knight Fork", "Feed Me Jack")
)

