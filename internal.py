import requests
import json
import datetime

from utilities import get_token, get_cookies

"""
Relevant Internal APIs:
    - Buddy List: https://guc-spclient.spotify.com/presence-view/v1/buddylist
    - Playlist Tree: https://spclient.wg.spotify.com/playlist/v2/user/6rcq1j21davq3yhbk1t0l5xnt/rootlist/changes
"""

if __name__ == "__main__":
    print({"Cookie": ",".join(f"{k}={v}" for k, v in get_cookies().items())})
    access_token = requests.get(
        'https://open.spotify.com/get_access_token?reason=transport&productType=web_player',
        headers={
            "Cookie": ",".join(f"{k}={v}" for k, v in get_cookies().items())
        }
    ).json()

    client_token = requests.post(
        "https://clienttoken.spotify.com/v1/clienttoken",
        headers={
            "Accept":"application/json",
            "Content-Type":"application/json"
        },
        data=json.dumps({
            "client_data": {
                "client_id": access_token['clientId'],
                "client_version": "1.2.27.93.g7aee53d4",
                "js_sdk_data": {
                    "device_brand": "Apple",
                    "device_model": "unknown",
                    "os": "macos",
                    "os_version": "10.15.7",
                    "device_id": "bdf5b14ba68e49870c47dfe3917aef28",
                    "device_type": "computer"
                }
            }
        })
    ).json()

    FOLDER_ID = "b03dee60f3e84bbc"
    present = datetime.datetime.now().timestamp()
    data = [
        {
            "ops": [
                {
                    "kind": 2,
                    "add": {
                        "items": [
                            {
                                "uri": f"spotify:start-group:{FOLDER_ID}:frick+it+we+ball",
                                "attributes": {
                                    "timestamp": present,
                                    "formatAttributes": [],
                                    "availableSignals": []
                                }
                            },
                            {
                                "uri": f"spotify:end-group:{FOLDER_ID}",
                                "attributes": {
                                    "timestamp": present,
                                    "formatAttributes": [],
                                    "availableSignals": []
                                }
                            }
                        ],
                        "addFirst": True
                    }
                }
            ],
            "info": {
                "source": {
                    "client": 5
                }
            }
        }
    ]

    UID = "6rcq1j21davq3yhbk1t0l5xnt"

    print(requests.post(
        f"https://spclient.wg.spotify.com/playlist/v2/user/{UID}/rootlist/changes",
        headers={
            "Authorization": f"Bearer {access_token['accessToken']}"
        },
        data=json.dumps({
            "baseRevision": "",
            "deltas": data,
            "nonces": [],
            "wantResultingRevisions": True,
            "wantSyncResult": False
        })
    ))

    # print(len(resp['friends']))
