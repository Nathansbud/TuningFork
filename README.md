# TuningFork

A collection of projects related to music files: lyric scraping, iTunes parsing, play logging, tag modification, Twitter lyric bots, and more! Everything is for personal use, so a tad rough around the edges (and everywhere else, to be honest):

- **Cleanser**: CLI tool to remove unwanted ID3 tags from MP3 files
- **Logger**: Script to read differences in iTunes Library.xml, and log change
- **Lyrical**: Lyric grabber from random/specified songs
- **LyricBot**: Script used to post random lyrics to Twitter for various artist bots, using Genius/Google Doc/Sheets as source
- **Migrator**: Spotify playlist creator from iTunes or tracks by name/artist
- **Parser**: Script to run through iTunes Library.xml file to load in song data, or query iTunes Library via Swift executable
- **Plotter**: Fun scripts to plot Logger data via matplotlib
- **Profane**: CLI tool to check if track lyrics contain profanity and build profanity-free playlist
- **Scraper**: Lyric scraper from Genius to update lyric tag of all songs specified as having scrapable vocals (Vocal in comments)
- **Turntable**: Custom track start/stop point and auto-queue manager for Spotify
    - **Jockey**: CLI tool to create Turntable rules (stored in `resources/rules.json`)
