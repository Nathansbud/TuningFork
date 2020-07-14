from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support import expected_conditions as EC

import os
import json
import time

import re

from requests_oauthlib import OAuth2, OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

from parser import get_vocal_tracks
from scraper import genius_clean

"""
Dear Future Me,

You will open this thinking "that is dumb, why did he do that"; Spotify is dumb, and also I am bad at WebDriverWait.

Please do not refactor things stupidly because you are stupid. Thanks.

If you DO want to investigate something, look into actually using the Spotify API ya dingus.
"""

feat_split = [" ft\. ", " feat\. ", " featuring\. ", " \(with "]
cred_path = os.path.join(os.path.dirname(__file__), "credentials")

def spotify_clean(field):
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
    with open(os.path.join(cred_path,"spotify.json")) as jf:
        creds = json.load(jf)

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

def manual_populate_playlist(browser, start_point=None, playlist_name=""):
    tracks = get_vocal_tracks()
    sp = 0
    if start_point and len(start_point) == 2:
        for i, t in enumerate(tracks):
            if t['Artist'] == start_point[0] and t['Name'] == start_point[1]:
                sp = i
                break

    for track in tracks[sp:]:
        action = ActionChains(browser)
        """
        search_box = browser.find_element_by_xpath("//input[@data-testid='search-input']")
        search_box.clear()
        search_box.send_keys(spotify_clean(track['Artist']) + " " + track['Name'] + "\n")
        """
        #abysmally slow, but ensures the page loads
        search_query = (spotify_clean(track['Artist']) + ' ' + track['Name']).replace('/', " ").replace("?", "")

        browser.get(f"https://open.spotify.com/search/{search_query.replace(' ', '%20')}")
        try:
            no_match = browser.find_element_by_xpath("//h1[starts-with(text(), 'No results found for')]")
        except NoSuchElementException:
            WebDriverWait(browser, 20).until(EC.text_to_be_present_in_element_value((By.XPATH, "//input[@data-testid='search-input']"),search_query))
            try:
                song_menu = browser.find_element_by_xpath("//section[@aria-label='Songs']")
                song_item = WebDriverWait(song_menu, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "react-contextmenu-wrapper")))
                action.context_click(song_item).perform()
                WebDriverWait(browser, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[text()='Add to Playlist']"))).click()
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "cover-art--with-auto-height"))).click()
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@aria-live='polite']")))
            except StaleElementReferenceException:
                print(f"somefin failed on {track['Name']}")
                pass
            except TimeoutException:
                print(f"somefin failed with timout stuff on {track['Name']}")
        else:
            print("No matches found")
            continue

def manual_migrate(start_point=None):
    b = make_browser(False)
    spotify_login(b)
    manual_populate_playlist(b, start_point=start_point)

def authorize_spotify():
    with open(os.path.join(cred_path,  "spotify.json")) as jf: creds = json.load(jf)

    scope = []
    spotify = OAuth2Session(creds['client_id'], scope=None, redirect_uri=creds['redirect_uri'])
    authorization_url, state = spotify.authorization_url(creds['authorization_url'], access_type="offline")
    print(f"Authorize at {authorization_url}")
    redirect_response = input("Paste redirect URL here: ")
    token = spotify.fetch_token(creds['token_url'], client_secret=creds['client_secret'], code=redirect_response)
    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)

    return spotify


def save_token(token):
    with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)


def migrate_library():
    with open(os.path.join(cred_path,  "spotify.json")) as jf: creds = json.load(jf)
    if not os.path.isfile(os.path.join(cred_path, "spotify_token.json")):
        spotify = authorize_spotify()
    else:
        """
        client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
        auto_refresh_kwargs = extra, token_updater = token_saver)
        
        """
        with open(os.path.join(cred_path, "spotify_token.json"), 'r+') as t: token = json.load(t)
        spotify = OAuth2Session(creds['client_id'], token=token)
        try:
            spotify.get("https://api.spotify.com/v1/tracks/2TpxZ7JUBn3uw46aR7qd6V")
        except TokenExpiredError as e:
            token = spotify.refresh_token(creds['token_url'], **{'client_id':creds['client_id'], 'client_secret':creds['client_secret']})
            with open(os.path.join(cred_path, "spotify_token.json"), 'w+') as t: json.dump(token, t)
        spotify = OAuth2Session(creds['client_id'], token=token)


if __name__ == '__main__':
    migrate_library()