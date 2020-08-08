from subprocess import Popen, PIPE

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

def start_server(port):
    httpd = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket,
                                   certfile=os.path.join(os.path.dirname(__file__), "certificates", "nathansbud.crt"),
                                   keyfile=os.path.join(os.path.dirname(__file__), "certificates", "nathansbud.key"),
                                   server_side=True)
    httpd.serve_forever()


def call_applescript(script):
    p = Popen(['osascript'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    return {"output": stdout, "error": stderr,"code": p.returncode}

def get_vocal_paths():
    get_tracks = """
    tell application "iTunes"
        set vocalPaths to (get location of (every track in library playlist 1 whose (comment is "Vocal")))
        repeat with i from 1 to (count vocalPaths)
            set item i of vocalPaths to (POSIX path of item i of vocalPaths)
        end repeat
        set vocalPOSIX to vocalPaths
    end tell
    """
    return [f"/{s.lstrip('/')}".strip() for s in call_applescript(get_tracks)['output'].split(", /")]

if __name__ == '__main__':
    start_server(6813)