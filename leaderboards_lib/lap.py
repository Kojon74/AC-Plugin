import time
import math
import csv

import urllib.parse

from leaderboards_lib.api import fetch

DOMAIN = "https://delta-flax.vercel.app"

FIELDS = ["distance_offset", "time_elapsed", "speed", "throttle", "brake", "gear", "drs", "rpm"]

import os, os.path

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w', newline='')

class Lap:
    def __init__(self, circuit):
        self.circuit = circuit # Pass as parameter so we don't need to check every lap
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
        data = {"lapTime": self.lap_time, "circuit": self.circuit["_id"], "sectorTimes": self.sector_times, "timestamp": timestamp, "user": {"_id": cur_user["_id"], "username": cur_user["username"]}}
        fetch("laps", "POST", data)

    # TODO: Make a call to fetch instead
    def upload_telemetry(self, cur_user_id, timestamp):
        f_path = "best_laps\{}\{}\{}.csv".format(cur_user_id, self.circuit["circuitName"], timestamp)
        with safe_open_w(f_path) as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(self.telemetry)
        with open(f_path, 'rb') as f:
            telemetry = f.read()
        req = urllib.request.Request(url='{}/api/telemetry/{}/{}/{}'.format(DOMAIN, cur_user_id, self.circuit["_id"], timestamp), data=telemetry, method="POST")
        with urllib.request.urlopen(req) as response:
            print(response.read())
