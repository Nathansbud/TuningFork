from utilities import get_token, get_library_albums
from datetime import datetime

spotify = get_token()

def save_album_history(year, allpath, yearpath):
    albums = get_library_albums(datetime(year, 1, 1, 0, 0, 0), client=spotify)[::-1]
    
    def name_fmt(alb, added, release=False):
        alb_name = alb['name']
        alb_artist = " & ".join([art['name'] for art in alb['artists']])
        alb_added = added.strftime("%B %d").replace(" 0", " ")
        alb_release = f' ({alb["release_date"]})' if release else ''

        return f'{alb_added} - {alb_name} by {alb_artist}{alb_release}\n'
    
    with open(allpath, "w+") as allf:
        for (alb, added) in albums:
            allf.write(name_fmt(alb, added))
    
    with open(yearpath, "w+") as yearf:
        for (alb, added) in [a for a in albums if a[0]['release_date'].startswith(f"{year}")]:
            yearf.write(name_fmt(alb, added, release=True))
