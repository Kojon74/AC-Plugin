# AC runs on Python 3.3.5
import urllib.request
import json
import os
import bisect
from datetime import datetime

import ac
import acsys

from sim_info import info

from leaderboards_lib import lap
from leaderboards_lib import leaderboards_ui
from leaderboards_lib.api import fetch, read_csv

# Third party libs
import numpy as np

IP_ADDRESS = "10.0.0.153"
TRACK_NAMES = {"bahrain_2020": "Bahrain International Circuit", "jeddah21": "Jeddah Corniche Circuit", "rt_suzuka": "suzuka-international-racing-course", "actk_losail_circuit": "Losail International Circuit", "acu_cota_2021": "Circuit of the Americas", "acu_mexico_2021": "Autódromo Hermanos Rodríguez", "melbourne22": "albert-park-circuit"}
# Default time if user hasn't set valid time on the selected track
DEFAULT_TIME = 999999999

class Leaderboards:
    def __init__(self):
        app_window = ac.newApp("Performance Delta")
        self.track = self.get_track()
        self.lap = lap.Lap(self.track)
        self.first_lap = True
        self.last_time = 0 # Used top keep track of new lap
        self.lap_count = 0
        self.users = self.get_users()
        self.cur_user = self.get_most_recent_user()
        self.best_lap_offset, self.best_lap_elapsed, self.best_lap_time = self.get_best_lap()
        self.ui = leaderboards_ui.LeaderboardsUI(app_window, self.cur_user, self.users, 0)

    def get_track(self):
        resp = fetch("tracks/{}".format(TRACK_NAMES[ac.getTrackName(0)]), "GET")
        return resp["track"]

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
            cur_username, cur_user_id = response['name'], response['userID']
            best_lap_path = 'best_laps\{}\{}'.format(cur_user_id, self.track)
            if not os.path.isdir(best_lap_path):
                os.makedirs(best_lap_path)
            return cur_username, cur_user_id

    def get_users(self):
        resp = fetch("users", "GET")
        return resp['users']
        
    def get_most_recent_user(self):
        most_recent_user = max(self.users, key=lambda x: x["lastOnline"])
        fetch("users/{}".format(most_recent_user["_id"]), "PUT")
        return most_recent_user

    def get_best_lap(self):
        # Check if user has set a time on this track
        resp_lap = fetch("laps/{}/{}/best".format(self.track["_id"], self.cur_user["_id"]), "GET")
        best_lap = resp_lap["bestLap"]
        if best_lap:
            dt_object = datetime.strptime(resp_lap["bestLap"]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            epoch = datetime(1970,1,1)
            timestamp = int((dt_object-epoch).total_seconds()*1000)
            resp_tel = fetch("telemetry/{}/{}/{}".format(self.cur_user["_id"], self.track["_id"], timestamp), "GET")
            headers, data = read_csv(resp_tel["telemetry"])
            offset = data[:,np.where(headers == "distance_offset")[0][0]]
            elapsed = data[:,np.where(headers == "time_elapsed")[0][0]]*1000
            return offset, elapsed, best_lap["lapTime"]
        return None, None, DEFAULT_TIME

    def update_delta(self, offset, elapsed):
        offset_i = bisect.bisect_left(self.best_lap_offset, offset)
        delta = elapsed - self.best_lap_elapsed[offset_i]
        self.ui.update_delta(delta)

    def check_invalidated(self):
        return info.physics.numberOfTyresOut > 2
    
    def get_cur_telemetry(self):
        offset = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
        elapsed = ac.getCarState(0, acsys.CS.LapTime)
        speed = ac.getCarState(0, acsys.CS.SpeedKMH)
        throttle =  ac.getCarState(0, acsys.CS.Gas)
        brake =  ac.getCarState(0, acsys.CS.Brake)
        gear =  ac.getCarState(0, acsys.CS.Gear)
        drs =  ac.getCarState(0, acsys.CS.DrsEnabled)
        rpm =  ac.getCarState(0, acsys.CS.RPM)
        return offset, elapsed, speed, throttle, brake, gear, drs, rpm
            
    def acMain(self, ac_version):
        return "Leaderboards"

    def acUpdate(self, deltaT):
        cur_time = ac.getCarState(0, acsys.CS.LapTime)
        # Check if new lap
        if cur_time < self.last_time:
            if not self.first_lap:
                last_lap_time = ac.getCarState(0, acsys.CS.LastLap)
                offset, elapsed, speed, throttle, brake, gear, drs, rpm = self.get_cur_telemetry()
                self.lap.add(1, last_lap_time, speed, throttle, brake, gear, drs, rpm)
                last_sector_times = ac.getLastSplits(0)
                self.lap.lap_time = last_lap_time
                self.lap.sector_times = last_sector_times
                is_best_lap = not self.lap.invalidated and self.lap.lap_time < self.best_lap_time
                if is_best_lap:
                    self.best_lap_time = self.lap.lap_time
                    telemetry = list(zip(*self.lap.telemetry))
                    self.best_lap_offset, self.best_lap_elapsed = list(telemetry[0]), list(telemetry[1])
                    self.ui.update_best_lap_time(self.best_lap_time)
                if not self.lap.invalidated:
                    self.lap.upload(self.cur_user)
            self.lap_count = ac.getCarState(0, acsys.CS.LapCount)
            self.lap = lap.Lap(self.track)
            self.ui.update_invalidated(False)
            self.ui.update_lap_counter(self.lap_count)
            self.first_lap = False
        if self.check_invalidated():
            self.lap.invalidated = True
            self.ui.update_invalidated(True)
        offset, elapsed, speed, throttle, brake, gear, drs, rpm = self.get_cur_telemetry()
        if self.best_lap_time != DEFAULT_TIME:
            self.update_delta(offset, elapsed)
        self.lap.add(offset, elapsed, speed, throttle, brake, gear, drs, rpm)
        self.ui.update_lap_time(ac.getCarState(0, acsys.CS.LapTime))
        self.last_time = cur_time

    def acShutdown(self):
        pass

leaderboards_app = Leaderboards()