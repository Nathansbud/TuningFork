#!/usr/local/opt/python/bin/python3.7

import tweepy
import json
import requests
import os

import random

from lyrical import lyrics_from_genius_by_url
from lyrical import show_lyrics

from googleapi import make_snippet_list_from_sheet
from googleapi import make_snippet_list_from_doc

char_limit = 280
artist_ids = {
    "Kero Kero Bonito":"231956",
    "Death Grips":"11778"
}

bot_uids = {
    "Kero Kero Botnito":"1153421304315310080",
    "Daily Grips":"1153750067133575168",
    "Botgenius":"1113132654596063238"
}

base_url = 'https://api.genius.com'

#Load creds for Twitter & Genius APIs
with open(os.path.join(os.path.dirname(__file__), "credentials" + os.sep + "secret.json")) as jf:
    creds = json.load(jf)

def setup_user(api_user):
    auth = tweepy.OAuthHandler(creds[api_user]['api_key'], creds[api_user]['api_secret'])
    auth.set_access_token(creds[api_user]['access_token'], creds[api_user]['access_secret'])
    return tweepy.API(auth)


def get_artist_songs(aid): #Wholesale stolen from https://www.jw.pe/blog/post/quantifying-sufjan-stevens-with-the-genius-api-and-nltk/
    url = base_url + "/artists/" + aid + "/songs"
    token = "Bearer " + creds["genius"]["access_token"]
    headers = {"Authorization": token}

    current_page = 1
    next_page = True
    songs = []

    while next_page:
        response = requests.get(url=url, params={"page":current_page}, headers=headers).json()
        page_songs = response['response']['songs']

        if page_songs:
            songs += page_songs
            current_page += 1
        else:
            next_page = False

    return [s for s in songs if s["primary_artist"]['id'] == int(aid)]

def get_lyric_snippet(aid):
    passed = False

    if aid.isdigit():
        songs = get_artist_songs(aid)
    elif artist_ids.__contains__(aid):
        songs = get_artist_songs(artist_ids[aid])
    else:
        raise TypeError("Artist ID or shorthand cannot be found")

    lyrics = ""

    while not passed:
        song_choice = random.choice(songs)

        if song_choice['url'].endswith("lyrics"):
            lyrics = show_lyrics(lyrics_from_genius_by_url(song_choice['url']))
            lyric_string = ""
            for l in lyrics:
                lyric_string += l + "\n"
            if 0 < lyric_string.__len__() <= char_limit:
                return lyric_string.strip()



def make_tweet(user, content):
    setup_user(user).update_status(status=content)

def make_tweet_from_drive(name, src, kind="sheet", buffer=50):
    if kind.lower() == "sheet":
        snippet_list = make_snippet_list_from_sheet(src, "A1:2000")
    elif kind.lower() == "doc":
        snippet_list = make_snippet_list_from_doc(src)
    else:
        print("Source does not exist!")
        return

    with open(os.path.join(os.path.dirname(__file__), 'logs' + os.sep + name+'.txt'), 'a+') as lf:
        lf.seek(0)
        lines = (lf.read()).split("\n")
        if len(lines) >= buffer:
            lines = lines[-buffer:]

        index = random.randint(0, len(snippet_list) - 1)
        while lines.__contains__(index):
            index = random.randint(0, len(snippet_list) - 1)

        lf.write(str(index)+"\n")


    make_tweet(name, snippet_list[index])


def delete_tweet(user, tid):
    setup_user(user).destroy_status(tid)

def follow_user(user, fid):
    if fid.isdigit():
        setup_user(user).create_friendship(fid)
    elif bot_uids.__contains__(fid):
        setup_user(user).create_friendship(bot_uids[fid])
    else:
        print("No user exists with uid " + fid)

if __name__ == "__main__":
    make_tweet("kkb_twitter", get_lyric_snippet("Kero Kero Bonito"))
    make_tweet("dg_twitter", get_lyric_snippet("Death Grips"))
    pass
