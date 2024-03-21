import json
import urllib.request

IP_ADDRESS = "10.0.0.153"

def fetch(endpoint, method, data=None):
    data = json.dumps(data).encode('utf-8')
    req =  urllib.request.Request('http://{}:3000/api/{}'.format(IP_ADDRESS, endpoint), data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req) as resp:
        resp = json.loads(resp.read().decode(resp.info().get_param('charset') or 'utf-8'))
    return resp