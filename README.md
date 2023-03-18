# TuningFork

![](./media/demo.mov)

A collection of projects related to music: queue management, playlist migration, listening snapshots, and more. Everything was designed for personal use, so is a tad rough around the edges :)

# Core

The main projects in this repo are those that interface with Spotify and Last.fm, which I actively use (and thus often update with new features. These include:

- **Enqueue**: Add tracks (or groups of tracks) to Spotify queue
- **Lastly**: Create playlists from Last.fm data

# Setup

Everything in this repository was built to serve my personal needs, which primarily center around Spotify and Last.fm. Both platforms require various API keys to be added to `credentials/`, detailed below.  Otherwise, setup is as it would be for any Python project (install dependencies from `requirements.txt`).

## Spotify API

Before using Spotify-dependent tools (e.g. Enqueue, Turntable, Migrator), a token must be generated. Add a `spotify.json` file to `credentials`, and populate with `client_id`, `client_secret`, and `redirect_uri` corresponding with [a created Spotify app](https://developer.spotify.com/dashboard/). 

Authorization flow is a little jank, but you should only need to deal with it once. When trying to make a request without authentication, the provided `redirect_uri` will be used. From personal testing, a `localhost` redirect works even without spinning up the local server, as the relevant authentication information is passed as URL parameters which can be copied over (and no response actually needs to come from the server).

Regardless, if this is for some reason no longer the case, you can spin up a local server by running `utilities.py` (which will, by default, host a local server on port 6813), and set your Spotify app's redirect URI accordingly (e.g. `localhost:6813`). Follow the instructions given when trying to run a Spotify-dependent service for the first time, and you should be good to go. As is, the server requires certificate files (such that https requests work), so if need be create a `certificates/` folder and run the provided command to generate certificates :)

## Last.fm API

Last.fm is [fairly straightforward](https://www.last.fm/api/account/create); add your `api_key` and `api_secret` under `credentials/lastfm.json`, and you should be good to go.

## Preferences

If interfacing with Last.fm, a `LASTFM_USER` must be set in your preferences file. Further, for my Spotify usage, I maintain a primary playlist, [Muzack](https://open.spotify.com/playlist/2bQJC2lUa4pXkAt2qQejlx?si=d8f644fb726249ba), and a backlog playlist for albums I plan to listen to, [Zacklog](https://open.spotify.com/playlist/79mpaUsn0LPGUyCkBRnSgZ?si=7d8c16c7b73045d4). These are used by `enqueue` in the form of the `--save` flag (to save the current track to primary playlist), and the `--source` flag (which takes `LIBRARY` or `BACKLOG` as arguments). To use these features, add their playlist IDs (extractable from a URI of the form `spotify:playlist:id`) to the preferences file.

# Rest of the Owl

Many projects have fallen by the wayside in the time that this repo has housed musical miscellany. I've long since migrated away from iTunes, meaning projects dealing with local files haven't been tested in a several years. 

Tools reliant upon `iTunes Library.xml` won't be able to work with `Music.app` (which deprecated the XML interface), nor likely work with the `reader/TuneSwiftly` provided to query tracks in a users iTunes library via the Swift API. Further, scripts with web scraping components (e.g. `Lyrical`, which interfaces with Genius) were fragile to begin with, and have almost certainly been broken by site redesigns.

Unmaintained projects housed under the TuningFork umbrella include:

**iTunes**:
- **Logger**: Local iTunes listening tracker by monitoring changes to `iTunes Library.xml`
    - **Plotter**: Fun scripts to graph `Logger` data
- **Parser**: Load local music library from `iTunes Library.xml` or `Music.app` using a Swift exectuable

**Spotify**:

- **Migrator**: Spotify playlist creator from iTunes or tracks by name/artist
- **Profane**: Tool to check if track lyrics contain profanity and build classroom-friendly playlists
- **Turntable**: Custom track start/stop point and queue rules for Spotify
    - **Jockey**: CLI tool to create Turntable rules (stored in `resources/rules.json`)

**Other**: 

- **Cleanser**: CLI tool to remove unwanted ID3 tags from MP3 files
- **Scraper**: Tool to add lyrics to local files using Genius data
    - **Lyrical**: Lyric grabber using Genius for random/specified songs 
    - **LyricBot**: Create Twitter bots which post lyrics (using Genius, GDocs, or GSheets as a source)

