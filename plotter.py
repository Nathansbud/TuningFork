import json
import os
import matplotlib.pyplot as plt
from datetime import datetime, date
from pandas.plotting import register_matplotlib_converters

with open(os.path.join(os.path.dirname(__file__), "data", "log.txt"), "r") as lf: lines = [json.loads(l) for l in lf.readlines()]
lines.sort(key=lambda l: l['skip_date'] if 'skip_date' in l else l['play_date_utc'])
plot_folder = os.path.join(os.path.dirname(__file__), "plots")

register_matplotlib_converters()

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

def play_plot(*name_artist_pair):
    name_artist_pair = name_artist_pair[::-1]
    fig, ax = plt.subplots()
    plt.title("Song Comparisons")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plots = []
    colors = ['red', 'orange', '#FADA5e', 'green', 'blue', 'indigo', 'violet'][::-1]

    for idx, pair in enumerate(name_artist_pair):
        tracks = track_events(pair[0], pair[1])
        plays = [std(d['play_date_utc']) for d in tracks if "play_count" in d]
        plots.append(ax.plot_date(plays, [pair[0]]*len(plays), color=colors[idx]))

    ax.set_xlim(right=datetime.today())
    plt.gcf().autofmt_xdate()
    plt.show()
    fig.savefig(os.path.join(plot_folder, "song_comparisons.png"))

def time_plot():
    hours = {i:0 for i in range(0, 24)}
    for t in [std(d['play_date_utc']) for d in lines if "play_count" in d]:
        #offset UTC+5:30 (since i'm typically in mumbai)
        if 29 < t.minute < 60: hours[(t.hour+6)%24]+=1
        else: hours[(t.hour+5)%24]+=1

    #blue color gradient, #00n0n0, n from 0 to C then down to 1 (behavior of -|x-12|+12)
    colors = [f"#00{hex(-abs(i-12)+12)[-1]}0{hex(-abs(i - 12)+12)[-1]}0" for i in range(24)]
    fig, ax = plt.subplots()
    plt.bar(hours.keys(), hours.values(), color=colors)
    plt.xticks(list(hours.keys()))
    ax.set_xlim([-1, 24])
    plt.xlabel("Hours (Military)")
    plt.ylabel("Plays")
    plt.title("Plays Per Hour")
    plt.show()
    fig.savefig(os.path.join(plot_folder, "play_times.png"))



play_plot(
    ("Cooks", "Still Woozy"),
    ("What?", "A Tribe Called Quest"),
    ("Mr. Clean", "Yung Gravy"),
    ("Favorite Song", "Chance the Rapper ft. Childish Gambino"),
    ("Won't Trade", "Q-Tip"),
    ("Truth Hurts", "Lizzo"),
    ("Knight Fork", "Feed Me Jack")
)

time_plot()


