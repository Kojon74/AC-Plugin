import time
import math
import csv

import urllib.parse

from leaderboards_lib.api import fetch

IP_ADDRESS = "10.0.0.153"

FIELDS = ["distance_offset", "time_elapsed", "speed", "throttle", "brake", "gear", "drs", "rpm"]

import os, os.path

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w', newline='')

class Lap:
    def __init__(self, track):
        self.track = track # Pass as parameter so we don't need to check every lap
        self.invalidated = False
        self.lap_time = None
        self.sector_times = None
        self.telemetry = []
        self.last_offset = 0

    def add(self, offset, elapsed, speed, throttle, brake, gear, drs, rpm):
        if offset > self.last_offset:
            self.telemetry.append([float(offset), float(elapsed/1000), float(speed), float(throttle), float(brake), int(gear), drs, rpm])
            self.last_offset = offset

    def upload(self, cur_user):
        timestamp = math.floor(time.time() * 1000)
        self.upload_telemetry(cur_user["_id"], timestamp)
        data = {"lapTime": self.lap_time, "track": self.track["_id"], "sectorTimes": self.sector_times, "timestamp": timestamp, "user": {"id": cur_user["_id"], "name": cur_user["name"]}}
        fetch("laps", "POST", data)

    def upload_telemetry(self, cur_user_id, timestamp):
        f_path = "best_laps\{}\{}\{}.csv".format(cur_user_id, self.track["name"], timestamp)
        with safe_open_w(f_path) as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(self.telemetry)
        with open(f_path, 'rb') as f:
            telemetry = f.read()
        req = urllib.request.Request(url='http://{}:3000/api/telemetry/{}/{}/{}'.format(IP_ADDRESS, cur_user_id, self.track["_id"], timestamp), data=telemetry, method="POST")
        with urllib.request.urlopen(req) as response:
            print(response.read())
