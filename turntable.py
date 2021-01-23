from utilities import get_token
import time
import os
import json
import sys

endpoints = {
    'playing': "https://api.spotify.com/v1/me/player/currently-playing",
    'user': "https://api.spotify.com/v1/me/",
    'skip': 'https://api.spotify.com/v1/me/player/next',
    'queue': 'https://api.spotify.com/v1/me/player/queue?uri={uri}',
    'scrub': "https://api.spotify.com/v1/me/player/seek?position_ms={to}"
}

class RuleManager:
    rule_file = os.path.join(os.path.dirname(__file__), "resources", "turntable.json")
    def __init__(self, user=None, rule_file=rule_file):
        self.spotify = get_token()
        if not user:
            self.user = self.spotify.get(endpoints['user']).json().get('id')
        
        self.rule_file = rule_file
        self.rules = self.update_rules()
        self.active_rule = {}

    def refresh_active(self, uri): 
        self.active_rule = {
            'uri': uri,
            'start': False,
            'end': False,
            'queue': False
        }
        
  
    def update_rules(self):
        self.rules = {}
        if os.path.isfile(self.rule_file):
            with open(self.rule_file, 'r+') as rf:    
                try:
                    self.rules = json.load(rf).get(self.user)
                except json.decoder.JSONDecodeError:
                    os.remove(RuleManager.rule_file)
                    self.update_rules()
        else: 
            with open(self.rule_file, 'w+') as rf:
                self.rules = {}
                json.dump({self.user: {}}, rf)    
        
        return self.rules
    
    def contains(self, uri): return uri in self.rules
    def poll(self):
        now_playing = self.spotify.get(endpoints.get('playing'))
        
        if now_playing.status_code == 200:        
            current = now_playing.json()
            track_uri = current.get('item', {}).get('uri')
            position = current.get('progress_ms')
            
            if self.active_rule.get('uri') != track_uri:
                self.refresh_active(track_uri)

            if self.contains(track_uri):
                self.apply_rule(track_uri, position)
        elif now_playing.status_code == 429:
            try:
                return int(now_playing.headers.get('Retry-After')) / 1000 + 1
            except ValueError:
                return None
    
    def forward(self): self.spotify.post(endpoints.get('skip'))
    def scrub(self, to): self.spotify.put(endpoints.get('scrub').format(to=to))
    def queue(self, uri): self.spotify.post(endpoints.get('queue').format(uri=uri))

    def apply_rule(self, uri, position):
        rule = self.rules.get(uri)
        if rule.get('queue') and not self.active_rule['queue']: 
            self.active_rule['queue'] = True
            self.queue(rule.get('queue'))
        
        if rule.get('start') and rule.get('start') > position:
            self.scrub(rule.get('start'))

        if rule.get('end') and rule.get('end') < position and not self.active_rule['end']:
            self.active_rule['end'] = True
            self.forward()
            self.active_rule['end'] = False
        
if __name__ == '__main__':
    manager = RuleManager()
    delay = 1
    count = 0
    try:
        while True:
            resp = manager.poll()
            time.sleep(1 if not resp else resp)
            count += 1
            if count > 120:
                manager.update_rules()
                count = 0
    except KeyboardInterrupt:
        print("Exiting...")
        exit(1)