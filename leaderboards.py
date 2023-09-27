import sys
import os
import platform

if platform.architecture()[0] == "64bit":
  sysdir = "stdlib64"
else:
  sysdir = "stdlib"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), sysdir))
os.environ['PATH'] = os.environ['PATH'] + ";."

from leaderboards_lib.leaderboards_lib import leaderboards_app

def acMain(ac_version):
  return leaderboards_app.acMain(ac_version)

def acUpdate(deltaT):
  leaderboards_app.acUpdate(deltaT)

def acShutdown():
  leaderboards_app.acShutdown()