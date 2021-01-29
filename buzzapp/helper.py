import json


def playerlist_to_json(plist):
    def func(p): return dict(p.__dict__, pts=p.get_points())
    return json.loads(json.dumps(plist, default=func))


def host_to_json(host):
    return json.loads(json.dumps(host, default=lambda obj: obj.__dict__))
