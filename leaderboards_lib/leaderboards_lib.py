# AC runs on Python 3.3.5
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
CIRCUIT_TAGS = {
    "bahrain_2020": "Bahrain International Circuit", 
    "jeddah21": "Jeddah Corniche Circuit", 
    "rt_suzuka": "suzuka-international-racing-course", 
    "actk_losail_circuit": "Losail International Circuit", 
    "acu_cota_2021": "Circuit of the Americas", 
    "acu_mexico_2021": "Autódromo Hermanos Rodríguez", 
    "melbourne22": "Australian"
}
# Default time if user hasn't set valid time on the selected circuit
DEFAULT_TIME = 999999999

class Leaderboards:
    def __init__(self):
        app_window = ac.newApp("Performance Delta")
        self.circuit = self.get_circuit()
        self.lap = lap.Lap(self.circuit)
        self.first_lap = True
        self.last_time = 0 # Used top keep circuit of new lap
        self.lap_count = 0
        self.users = self.get_users()
        self.get_most_recent_user()
        self.best_lap_offset, self.best_lap_elapsed, self.best_lap_time = self.get_best_lap()
        self.ui = leaderboards_ui.LeaderboardsUI(app_window, self.cur_user, self.users, 0, self.set_cur_user)

    def set_cur_user(self, user):
        self.cur_user = user

    def get_circuit(self):
        resp = fetch("circuits/{}".format(CIRCUIT_TAGS[ac.getTrackName(0)]), "GET")
        return resp["circuit"]

    def get_users(self):
        resp = fetch("users", "GET")
        return resp['users']
        
    def get_most_recent_user(self):
        most_recent_user = max(self.users, key=lambda x: x["lastOnline"])
        fetch("users/{}".format(most_recent_user["username"]), "PUT")
        self.set_cur_user(most_recent_user)

    def get_best_lap(self):
        # Check if user has set a time on this circuit
        resp_lap = fetch("laps/{}/{}/best".format(self.circuit["_id"], self.cur_user["_id"]), "GET")
        best_lap = resp_lap["bestLap"]
        if best_lap:
            dt_object = datetime.strptime(resp_lap["bestLap"]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            epoch = datetime(1970,1,1)
            timestamp = int((dt_object-epoch).total_seconds()*1000)
            resp_tel = fetch("telemetry/{}/{}/{}".format(self.cur_user["_id"], self.circuit["_id"], timestamp), "GET")
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
            self.lap = lap.Lap(self.circuit)
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