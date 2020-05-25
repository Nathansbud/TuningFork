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

from parser import get_vocal_tracks
from scraper import genius_clean

"""
Dear Future Me,

You will open this thinking "that is dumb, why did he do that"; it is because Spotify is dumb, and also I am bad at WebDriverWait.

Please do not refactor things stupidly because you are stupid. Thanks.

If you DO want to investigate something, look into actually using the Spotify API ya dingus.
"""

feat_split = [" ft\. ", " feat\. ", " featuring\. ", " \(with "]

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
    with open(os.path.join(os.path.dirname(__file__), "credentials", "spotify.json")) as jf: creds = json.load(jf)

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

if __name__ == "__main__":
    b = make_browser(False)
    spotify_login(b)
    manual_populate_playlist(b, start_point=("King Crimson", "Easy Money"))

