import os
import json

prefs_file = os.path.join(os.path.dirname(__file__), "resources", "preferences.json")
group_file = os.path.join(os.path.dirname(__file__), "resources", "groups.json")
shortcuts_file = os.path.join(os.path.dirname(__file__), "resources", "shortcuts.json")

# TODO: Synced-style class for preferences/groups
def load_prefs():
    if not os.path.isfile(group_file):
        with open(group_file, 'w+') as gf: json.dump({}, gf)

    if not os.path.isfile(prefs_file):              
        with open(prefs_file, 'w+') as pf: json.dump({
                "PLAYLISTS": {
                    "DEFAULT": "",
                    "PRIMARY": "",
                    "BACKLOG": "",
                    "SHARED": ""
                },
                "ALIASES": {},
                "LASTFM_USER": "",
                "LASTFM_WATCH_USER": "Nathansbud"
            }, pf)
    
    if not os.path.isfile(shortcuts_file):
        with open(shortcuts_file, 'w+') as sf: 
            json.dump(
                {"albums": {}, "tracks": {}},
                sf
            )

    with \
        open(group_file, 'r') as gf, \
        open(prefs_file, 'r') as pf, \
        open(shortcuts_file, 'r') as sf:
        
        try:
            gs = json.load(gf)
        except Exception: 
            gs = {}
        
        try: 
            ps = json.load(pf)
        except Exception:
            ps = {}
        
        try:
            ss = json.load(sf)
        except Exception:
            ss = {}

        return gs, ps, ss

def dump_groups():
    with open(group_file, 'w+') as gf: 
        json.dump(groups, gf)

def dump_shortcuts():
    with open(shortcuts_file, 'w+') as sf:
        json.dump(shortcuts, sf)

groups, prefs, shortcuts = load_prefs()