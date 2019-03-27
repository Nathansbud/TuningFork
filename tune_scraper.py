from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

from parser import parse_itunes_xml

arr = parse_itunes_xml()
###CODE THAT IS NOT MINE STARTS HERE:
def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

###ENDS HERE—THANK YOU TO

##To-do: Try-catch block in case genius page doesn't exist (so it doesn't crash the ones that do) with a log file, output lyrics to text files using itunes filepath
##also how to deal with features? Genius scraping won't work with them...
def get_lyrics(artist, name):
    artist = artist.lower().replace(" ", "-").capitalize().replace("•", "").replace("!", "-")
    name = name.lower().replace(" - ", "-").replace(" ", "-").replace(".", "").replace("!", "").replace("'", "").replace("/", "-").replace(",", "").replace("?", "").replace("(", "").replace(")", "").replace("’", "").replace(":", "")
    #to-do, clean up the above to use regex...was just trying POC and will clean up later

    print("https://genius.com/" + artist + "-" +  name + "-lyrics")

    raw_html = simple_get("https://genius.com/" + artist + "-" +  name + "-lyrics")

    soup = BeautifulSoup(raw_html, 'html.parser')
    soup.prettify()

    tags = soup.find(class_="lyrics")
    print(tags.text)

for s in arr:
    if "Comments" in s:
        if "Vocal" in s["Comments"]:
            get_lyrics(s["Artist"], s["Name"])

# print(arr)


if __name__ == "__main__":
    get_lyrics("Gentle Giant", "In a Glass House")
    pass