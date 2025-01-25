import json
import urllib.request
import csv
from io import StringIO

import ac

import numpy as np

DOMAIN = "https://delta-flax.vercel.app" # http instead of https because of missing ssl module

def fetch(endpoint, method, data=None):
    data = json.dumps(data).encode('utf-8')
    try:
        req =  urllib.request.Request('{}/api/{}'.format(DOMAIN, endpoint), data=data, headers={"Content-Type": "application/json"}, method=method)
        with urllib.request.urlopen(req) as resp:
            resp = json.loads(resp.read().decode(resp.info().get_param('charset') or 'utf-8'))
        return resp
    except urllib.error.HTTPError as e:
        if e.code == 308:
            new_url = e.headers["Location"]  # Extract the redirect URL
            resp = urllib.request.urlopen(new_url)
            resp = json.loads(resp.read().decode(resp.info().get_param('charset') or 'utf-8'))
            return resp
        else:
            ac.log("HTTP Error: {}".format(e))

def read_csv(data):
    csv_data = list(csv.reader(StringIO(data)))
    return np.array(csv_data[0]), np.asarray(csv_data[1:], dtype=np.float)