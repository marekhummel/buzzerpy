import json


def playerlist_to_json(plist):
    return json.loads(json.dumps(plist, default=lambda obj: obj.__dict__))
