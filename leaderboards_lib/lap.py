import urllib.request
import time
import math
import csv

import ac

IP_ADDRESS = "10.0.0.153"

FIELDS = ["distance_offset", "time_elapsed"]

class Lap:
    def __init__(self, track):
        self.track = track # Pass as parameter so we don't need to check every lap
        self.invalidated = False
        self.lap_time = None
        self.sector_times = None
        self.distance_time = []

    def add(self, offset, elapsed):
        self.distance_time.append([float(offset), int(elapsed)])

    def upload(self, cur_user_id, is_best_lap):
        timestamp = math.floor(time.time() * 1000)
        data = urllib.parse.urlencode({"lap_time": self.lap_time, "track": self.track, "invalidated": self.invalidated, "sector_times": self.sector_times, "timestamp": timestamp, "is_best_lap": is_best_lap}).encode("ascii")
        req = urllib.request.Request(url='http://{}:8000/upload-lap/'.format(IP_ADDRESS), data=data)
        with urllib.request.urlopen(req) as response:
            print(response.read())
        with open("best_laps\{}\{}\{}.csv".format(cur_user_id, self.track, timestamp), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(self.distance_time)