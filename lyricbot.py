import tweepy
import json
import requests

from random import choice
from scraper import get_lyrics_from_url

#Load creds for Twitter & Genius APIs
with open("secret.json") as jf:
    creds = json.load(jf)

#Authorize Twitter API
auth = tweepy.OAuthHandler(creds['twitter']['api_key'], creds['twitter']['api_secret'])
auth.set_access_token(creds['twitter']['access_token'], creds['twitter']['access_secret'])
api = tweepy.API(auth)



#api.update functions return the Tweet object that was created, thus doing getattribute(_json)["id"] the ID of said tweet can be retrieved

def update_bio(bio_str):
    api.update_profile(status=bio_str)

#tweet = api.update_status(status="owo")
#api.destroy_status(tweet.__getattribute__("_json")["id"])

#GENIUS SECTIOn

base_url = 'https://api.genius.com'
artist_ids = {
    "Kero Kero Bonito":"231956",
    "Death Grips":"11778"
}

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

songs = get_artist_songs(artist_ids["Kero Kero Bonito"])
song_choice = choice(songs)

print(get_lyrics_from_url(song_choice['url']))

if __name__ == "__main__":
    pass