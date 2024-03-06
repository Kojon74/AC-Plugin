import urllib.request
import json
import os
import bisect
import csv
import sys

import ac
import acsys

from sim_info import info

from leaderboards_lib import lap
from leaderboards_lib import leaderboards_ui

IP_ADDRESS = "10.0.0.153"
TRACK_NAMES = {"bahrain_2020": "Bahrain International Circuit", "jeddah21": "Jeddah Corniche Circuit", "rt_suzuka": "Suzuka Circuit", "actk_losail_circuit": "Losail International Circuit", "acu_cota_2021": "Circuit of the Americas", "acu_mexico_2021": "Autódromo Hermanos Rodríguez", "melbourne22": "Albert Park Circuit"}
DEFAULT_TIME = 999999999
# Default time is user hasn't set valid time on the selected track

class Leaderboards:
    def __init__(self):
        app_window = ac.newApp("Performance Delta")
        self.track = TRACK_NAMES[ac.getTrackName(0)]
        self.lap = lap.Lap(self.track)
        self.lap_count = 0
        self.cur_username, self.cur_user_id = self.init_server()
        self.best_lap_offset, self.best_lap_elapsed, self.best_lap_time = self.get_best_lap()
        self.ui = leaderboards_ui.LeaderboardsUI(app_window, self.cur_username, self.best_lap_time)

    '''
    Serves multiple purposes:
    1. Check if the server is up and running without errors
    2. Get's the current user from the server
    3. Updates the database to reflect current track
    '''
    def init_server(self):
        data = urllib.parse.urlencode({"track": self.track}).encode("ascii")
        with urllib.request.urlopen(url='http://{}:8000/app-boot/'.format(IP_ADDRESS), data=data) as response:
            response = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
            cur_username, cur_user_id = response['username'], response['userID']
            best_lap_path = 'best_laps\{}\{}'.format(cur_user_id, self.track)
            if not os.path.isdir(best_lap_path):
                os.makedirs(best_lap_path)
            return cur_username, cur_user_id

    def get_best_lap(self):
        data = urllib.parse.urlencode({"track": self.track}).encode("ascii")
        with urllib.request.urlopen('http://{}:8000/best-lap'.format(IP_ADDRESS), data=data) as response:
            response = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
            best_lap_time = response['lapTime']
            best_lap_id = response['id']
        best_lap_dir = 'best_laps\{}\{}'.format(self.cur_user_id, self.track)
        if not os.path.isfile('{}\{}.csv'.format(best_lap_dir, best_lap_id)) or best_lap_time == 0:
            return None, None, DEFAULT_TIME
        with open('best_laps\{}\{}\{}.csv'.format(self.cur_user_id, self.track, best_lap_id), 'rb') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
        offset, elapsed = data[:,0], data[:,1]
        return offset, elapsed, best_lap_time

    def update_delta(self, offset, elapsed):
        offset_i = bisect.bisect_left(self.best_lap_offset, offset)
        delta = elapsed - self.best_lap_elapsed[offset_i]
        self.ui.update_delta(delta)

    def check_invalidated(self):
        return info.physics.numberOfTyresOut > 2
            
    def acMain(self, ac_version):
        return "Leaderboards"

    def acUpdate(self, deltaT):
        cur_lap_count = ac.getCarState(0, acsys.CS.LapCount)
        if cur_lap_count > self.lap_count:
            self.lap_count = cur_lap_count
            last_lap_time = ac.getCarState(0, acsys.CS.LastLap)
            last_sector_times = ac.getLastSplits(0)
            self.lap.lap_time = last_lap_time
            self.lap.sector_times = last_sector_times
            is_best_lap = not self.lap.invalidated and self.lap.lap_time < self.best_lap_time
            if is_best_lap:
                self.best_lap_time = self.lap.lap_time
                distance_time = list(zip(*self.lap.distance_time))
                self.best_lap_offset, self.best_lap_elapsed = list(distance_time[0]), list(distance_time[1])
                self.ui.update_best_lap_time(self.best_lap_time)
            self.lap.upload(self.cur_user_id, is_best_lap)
            self.lap = lap.Lap(self.track)
            self.ui.update_invalidated(False)
            self.ui.update_lap_counter(self.lap_count)
        if self.check_invalidated():
            self.lap.invalidated = True
            self.ui.update_invalidated(True)
        offset = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
        elapsed = ac.getCarState(0, acsys.CS.LapTime)
        if self.best_lap_time != DEFAULT_TIME:
            self.update_delta(offset, elapsed)
        # ac.log(type(offset))
        # ac.log(offset)
        self.lap.add(offset, elapsed)
        self.ui.update_lap_time(ac.getCarState(0, acsys.CS.LapTime))

    def acShutdown(self):
        req = urllib.request.Request(url='http://{}:8000/app-shutdown/'.format(IP_ADDRESS))
        with urllib.request.urlopen(req) as response:
            response = ac.log("Shutdown: {}".format(response.read()))

leaderboards_app = Leaderboards()