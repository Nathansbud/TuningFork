from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.action_chains import ActionChains

import os
import json
from parser import get_vocal_tracks
from scraper import genius_clean
import time
import re

feat_split = [" ft\. ", " feat\. ", " featuring\. ", " \(with "]
def spotify_clean(field):
    clean_features = re.split("|".join(feat_split), field)[0]
    clean_partners = clean_features.replace(" & ", " ")
    return clean_partners

with open(os.path.join(os.path.dirname(__file__), "credentials", "spotify.json")) as jf: creds = json.load(jf)

browser = webdriver.Chrome()
action = ActionChains(browser)
browser.get("https://open.spotify.com/search")
browser.implicitly_wait(5)

buttons = browser.find_elements_by_tag_name("button")

for b in buttons:
    if b.text.strip().lower() == "log in":
        b.click()
        browser.find_element_by_id("login-username").send_keys(creds['email'])
        browser.find_element_by_id("login-password").send_keys(creds['password'])
        browser.find_element_by_id("login-button").click()
        break
else: print("Already logged in; continuing")

for track in get_vocal_tracks():
    search_box = browser.find_element_by_xpath("//input[@data-testid='search-input']")
    search_box.clear()
    search_box.send_keys(spotify_clean(track['Artist']) + " " + track['Name'] + "\n")
    try:
        song_menu = search_box.find_element_by_xpath("//section[@aria-label='Songs']")
        song_item = song_menu.find_element_by_class_name("react-contextmenu-wrapper")
        song_item.click()
        time.sleep(0.2)
        song_item.find_element_by_xpath("//button[@aria-label='Context Menu Button']").click()
        browser.find_element_by_xpath("//div[text()='Add to Playlist']").click()
        browser.find_element_by_class_name("cover-art--with-auto-height").click()
    except:
        print(f"Track add failure on {track['Name']} by {track['Artist']}")
    # except selenium.common.exceptions.NoSuchElementException:
    #     print(f"Track add failure on {track['Name']} by {track['Artist']}")
    # except selenium.common.exceptions.ElementClickInterceptedException:
    #     print(f"Track add failure on {track['Name']} by {track['Artist']}")
    # except selenium.common.exceptions.StaleElementReferenceException:
    #     print(f"Track add failure on {track['Name']} by {track['Artist']}")
    finally:
        if not browser.current_url.startswith("https://open.spotify.com/search/"):
            browser.get("https://open.spotify.com/search")
        time.sleep(0.2)
if __name__ == "__main__":

    pass