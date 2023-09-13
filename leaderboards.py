import sys
import os
import platform
import json
import ac
import acsys

if platform.architecture()[0] == "64bit":
  sysdir = "stdlib64"
else:
  sysdir = "stdlib"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), sysdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

import urllib.request
from sim_info import info

ip_address = "10.0.0.153"

l_lapcount = 0
lapcount = 0
invalidated = False
track = ""
current_user = ""

def acMain(ac_version):
  global l_lapcount, track, current_user
  # Test server
  with urllib.request.urlopen('http://{}:8000/current-user'.format(ip_address)) as response:
    current_user = json.loads(response.read().decode(response.info().get_param('charset') or 'utf-8'))
    current_user = current_user['username']
  appWindow = ac.newApp("Leaderboards")
  ac.setSize(appWindow, 200, 200)
  l_cur_user = ac.addLabel(appWindow, "{}".format(current_user))
  ac.setPosition(l_cur_user, 3, 30)
  l_lapcount = ac.addLabel(appWindow, "Lap Time: 0")
  ac.setPosition(l_lapcount, 3, 50)
  track = ac.getTrackName(0)
  return "Leaderboards"

def acUpdate(deltaT):
  global l_lapcount, lapcount, invalidated, track
  laps = ac.getCarState(0,acsys.CS.LapCount)
  if laps > lapcount:
    lapcount = laps
    lap_time = ac.getCarState(0, acsys.CS.LastLap)
    send_lap_data(lap_time, track, invalidated)
    invalidated = False
    ac.setText(l_lapcount, "Lap Time: {}".format(lap_time))
  lap_invalidated = ac.getCarState(0, acsys.CS.LapInvalidated)
  if lap_invalidated:
    invalidated = True

def send_lap_data(lap_time, track, invalidated):
  data = urllib.parse.urlencode({"lap_time": lap_time, "track": track, "invalidated": invalidated}).encode("ascii")
  req = urllib.request.Request(url='http://{}:8000/upload-lap/'.format(ip_address), data=data)
  with urllib.request.urlopen(req) as response:
    print(response.read())
    ac.setText(l_lapcount, "Lap Time: {}".format(response.read()))