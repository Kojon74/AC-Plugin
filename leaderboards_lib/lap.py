import urllib.request
import pickle
import time

IP_ADDRESS = "10.0.0.153"

class Lap:
    def __init__(self, track):
        self.track = track # Pass as parameter so we don't need to check every lap
        self.invalidated = False
        self.lap_time = None
        self.sector_times = None

        self.offset = []
        self.elapsed = []

    def add(self, offset, elapsed):
        self.offset.append(offset)
        self.elapsed.append(elapsed)

    def upload(self, cur_user_id, is_best_lap):
        cur_time = time.time()
        data = urllib.parse.urlencode({"lap_time": self.lap_time, "track": self.track, "invalidated": self.invalidated, "sector_times": self.sector_times, "cur_time": cur_time}).encode("ascii")
        req = urllib.request.Request(url='http://{}:8000/upload-lap/'.format(IP_ADDRESS), data=data)
        with urllib.request.urlopen(req) as response:
            print(response.read())
        if is_best_lap:
            with open("best_laps\{}\{}\{}_offset".format(cur_user_id, self.track, cur_time), "wb") as fp:
                pickle.dump(self.offset, fp)
            with open("best_laps\{}\{}\{}_elapsed".format(cur_user_id, self.track, cur_time), "wb") as fp:
                pickle.dump(self.elapsed, fp)