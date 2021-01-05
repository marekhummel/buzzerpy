import json


def playerlist_to_json(plist):
    return json.loads(json.dumps(plist, default=lambda obj: obj.__dict__))


def host_to_json(host):
    return json.loads(json.dumps(host, default=lambda obj: obj.__dict__))
