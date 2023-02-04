# TuningFork

A collection of projects related to music files: lyric scraping, play logging, Last.fm snapshots, Spotify playlist migration, queue management, you name it! Everything is for personal use, so a tad rough around the edges (and everywhere else, to be honest):

- **Cleanser**: CLI tool to remove unwanted ID3 tags from MP3 files
- **Enqueue**: Add tracks (or groups of tracks) to Spotify queue
- **Logger**: Script to read differences in iTunes Library.xml, and log change
- **Lastly**: Create playlists from Last.fm data
- **Lyrical**: Lyric grabber from random/specified songs
- **LyricBot**: Script used to post random lyrics to Twitter for various artist bots, using Genius/Google Doc/Sheets as source
- **Migrator**: Spotify playlist creator from iTunes or tracks by name/artist
- **Parser**: Script to run through iTunes Library.xml file to load in song data, or query iTunes Library via Swift executable
- **Plotter**: Fun scripts to plot Logger data via matplotlib
- **Profane**: CLI tool to check if track lyrics contain profanity and build profanity-free playlist
- **Scraper**: Lyric scraper from Genius to update lyric tag of all songs specified as having scrapable vocals (Vocal in comments)
- **Turntable**: Custom track start/stop point and auto-queue manager for Spotify
    - **Jockey**: CLI tool to create Turntable rules (stored in `resources/rules.json`)

# Setup

Everything in this repository was built to serve my personal needs. I used to utilize iTunes, then migrated over to Spotify. iTunes scripts should still work, but haven't been tested in years. Spotify and Last.fm scripts (namely: `enqueue.py`, `lastly.py`) require various API keys to be added to `credentials/`:

## Spotify API

Before using Spotify-dependent tools (e.g. Enqueue, Turntable, Migrator), a token must be generated. Add a `spotify.json` file to `credentials`, and populate with `client_id`, `client_secret`, and `redirect_uri` corresponding with [a created Spotify app](https://developer.spotify.com/dashboard/). 

Authorization flow is a little jank, but you should only need to deal with it once. You can spin up a local server by running `utilities.py` (by default, hosted on port 6813), and set your Spotify app's redirect URI accordingly (i.e. `localhost:6813`). Follow the instructions given when trying to run a Spotify-dependent service for the first time, and you should be good to go :)

## Last.fm API

Last.fm is [fairly straightforward](https://www.last.fm/api/account/create); add your `api_key` and `api_secret` under `credentials/lastfm.json`, and you should be good to go.

## Preferences

If interfacing with Last.fm, a `LASTFM_USER` must be set in your preferences file. Further, for my Spotify usage, I maintain a primary playlist, [Muzack](https://open.spotify.com/playlist/2bQJC2lUa4pXkAt2qQejlx?si=d8f644fb726249ba), and a backlog playlist for albums I plan to listen to, [Zacklog](https://open.spotify.com/playlist/79mpaUsn0LPGUyCkBRnSgZ?si=7d8c16c7b73045d4). These are used by `enqueue` in the form of the `--save` flag (to save the current track to primary playlist), and the `--source` flag (which takes `LIBRARY` or `BACKLOG` as arguments). To use these features, add their playlist IDs (extractable from a URI of the form `spotify:playlist:id`) to the preferences file.
