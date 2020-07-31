from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support import expected_conditions as EC

import os
import json
import time
from math import ceil

import re

from requests_oauthlib import OAuth2, OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

from parser import get_tracks
from unidecode import unidecode


feat_split = [" ft\. ", " feat\. ", " featuring\. ", " \(with "]
cred_path = os.path.join(os.path.dirname(__file__), "credentials")

playlists = {
    "all":"2bQJC2lUa4pXkAt2qQejlx",
    "Vibe Check":"7vCyHDvq0dBwbfsyZMwUIn",
    "Feel the Wooz":"3O2xBhsDTbYDCvrU4YAUcM",
    "Jackin' It":"3O2xBhsDTbYDCvrU4YAUcM",
    "New Directions":"392ZrJDVDuiCIaDQYNBqVw"
}

with open(os.path.join(cred_path, "spotify.json")) as jf: creds = json.load(jf)

def manual_clean(field):
    clean_features = re.split("|".join(feat_split), field)[0]
    clean_partners = clean_features.replace(" & ", " ")
    return clean_partners

def make_browser(headless=True, implicit_wait=3):
    options = webdriver.ChromeOptions()
    if headless: options.add_argument("headless")
    browser = webdriver.Chrome(options=options)
    if implicit_wait > 0: browser.implicitly_wait(implicit_wait)
    return browser

def spotify_login(browser):
    browser.get("https://open.spotify.com/search")
    buttons = browser.find_elements_by_tag_name("button")

    for button in buttons:
        if button.text.strip().lower() == "log in":
            button.click()
            browser.find_element_by_id("login-username").send_keys(creds['email'])
            browser.find_element_by_id("login-password").send_keys(creds['password'])
            browser.find_element_by_id("login-button").click()
            break
    else:
        print("Already logged in; continuing")

def spotify_clean(field):
    unicode_cleaned = unidecode(field)
    feat_cleaned = re.split("\sfeat\.\s|\sft\.\s|\sfeaturing\s", unicode_cleaned)[0]
    field_cleaned = re.sub(r"[^a-zA-Z0-9]", " ", feat_cleaned).strip()
    space_cleaned = re.sub(r"\s+", "+", field_cleaned)
    return space_cleaned.lower()


def authorize_spotify():
    scope = ["playlist-modify-private", "playlist-modify-public"]

    spotify = OAuth2Session(creds['client_id'], scope=scope, redirect_uri=creds['redirect_uri'])
    authorization_url, state = spotify.authorization_url(creds['authorization_url'], access_type="offline")
    print(f"Authorize at {authorization_url}")

    redirect_response = input("Paste redirect URL here: ")
    token = spotify.fetch_token(creds['token_url'], client_secret=creds['client_secret'], code=redirect_response)

    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)

    return spotify


def save_token(token):
    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)

def migrate_library(pid=playlists['all'], from_playlist=None, clear=False, tracks=[]):
    if not os.path.isfile(os.path.join(cred_path, "spotify_token.json")):
        spotify = authorize_spotify()
    else:
        with open(os.path.join(cred_path, "spotify_token.json"), 'r+') as t: token = json.load(t)
        spotify = OAuth2Session(creds['client_id'], token=token,
                                auto_refresh_url=creds['token_url'],
                                auto_refresh_kwargs={'client_id':creds['client_id'], 'client_secret':creds['client_secret']},
                                token_updater=save_token)

    if clear:
        spotify.put(f"https://api.spotify.com/v1/playlists/{pid}/tracks",
                    data=json.dumps({'uris':[]}),
                    headers={"Content-Type": "application/json"})


    playlist_uris = set()
    total_items = 100 #minimum tracks returned is 100
    has_updated = False
    i = 0
    while i < ceil(total_items / 100):
        playlist = spotify.get(f"https://api.spotify.com/v1/playlists/{pid}/tracks/?fields=total,items(track(uri))&offset={100*i}").json()
        if not has_updated:
            total_items = playlist['total']
            has_updated = True

        for it in [item['track']['uri'] for item in playlist['items']]:
            playlist_uris.add(it)

        i += 1
    track_uris = set()
    failed = set()
    add_tracks = lambda ts: spotify.post(f"https://api.spotify.com/v1/playlists/{pid}/tracks", data=json.dumps({"uris":list(ts)}), headers={"Content-Type": "application/json"})
    for track in (get_tracks(from_playlist)[::-1] if from_playlist else tracks): #Reverse to get newest first
        oname = track['Name'] if not tracks else track[0]
        oartist = track['Artist'] if not tracks else track[1]

        name = spotify_clean(oname)
        artist = spotify_clean(oartist)
        st = spotify.get(f"https://api.spotify.com/v1/search/?q={name}%20artist:{artist}&type=track&limit=1&offset=0").json()
        track_uri = st['tracks']['items'][0]['uri'] if st['tracks']['items'] else ""
        if track_uri and not track_uri in playlist_uris:
            track_uris.add(track_uri)
        elif not track_uri:
            print(f"Failed to add {oname} by {oartist}")
            failed.add(f"{oname} by {oartist}")

        if len(track_uris) >= 100:
            add_tracks(track_uris)
            track_uris = set()

    if len(track_uris) > 0: add_tracks(track_uris)
    with open(os.path.join(os.path.dirname(__file__), "data", "failed.txt"), "w+") as ff:
        ff.writelines(map(lambda l: l+"\n", list(failed)))

if __name__ == '__main__':
    pass
    # migrate_library(playlists['all'], "Vocal", False)
    # migrate_library(playlists['Vibe Check'], "Vibe Check", False)
    # with open(os.path.join(os.path.dirname(__file__), "data", "glee.json")) as gf:
    #     glee_tracks = json.load(gf)
    #     migrate_library(playlists['New Directions'], tracks=glee_tracks, clear=False)