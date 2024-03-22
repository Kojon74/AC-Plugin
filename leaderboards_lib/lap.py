import time
import math
import csv

from leaderboards_lib.api import fetch

IP_ADDRESS = "10.0.0.153"

FIELDS = ["distance_offset", "time_elapsed", "gas", "brake"]

class Lap:
    def __init__(self, track):
        self.track = track # Pass as parameter so we don't need to check every lap
        self.invalidated = False
        self.lap_time = None
        self.sector_times = None
        self.telemetry = []
        self.last_offset = 0

    def add(self, offset, elapsed, gas, brake):
        if offset > self.last_offset:
            self.telemetry.append([float(offset), float(elapsed/1000), float(gas), float(brake)])
            self.last_offset = offset

    def upload(self, cur_user_id):
        self.telemetry.append([1, self.lap_time/1000, 1.0, 0.0])
        timestamp = math.floor(time.time() * 1000)
        self.upload_telemetry(cur_user_id, timestamp)
        data = {"lapTime": self.lap_time, "trackId": self.track, "sectorTimes": self.sector_times, "timestamp": timestamp}
        fetch("laps", "POST", data)
        # data = urllib.parse.urlencode(telemetry).encode("ascii")
        # req = urllib.request.Request(url='http://{}:8000/upload-lap/'.format(IP_ADDRESS), data=data)
        # with urllib.request.urlopen(req) as response:
        #     print(response.read())

    def upload_telemetry(self, cur_user_id, timestamp):
        f_path = "best_laps\{}\{}\{}.csv".format(cur_user_id, self.track, timestamp)
        with open(f_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(self.telemetry)
        with open(f_path, 'rb') as f:
            telemetry = f.read()
        data = {"userId": cur_user_id, "trackId": self.track["_id"], "timestamp": timestamp, "telemetry": telemetry}
        fetch("telemetry", "POST", data)
